import pandas as pd
import pytest

from research.agent_policy import replay_policy


def sample():
    rows = []
    for lm in [.25, .5, .75]:
        for issue in range(6):
            rows.append(dict(project='P', sprint_id=1, issue_id=issue, landmark=lm,
                             y=int(issue < 3), p_raw=.9 - issue / 10,
                             dynamic_is_done=int(issue == 0 or (issue == 1 and lm >= .5)),
                             prediction_at=pd.Timestamp('2020-01-01', tz='UTC') + pd.Timedelta(days=12 * lm),
                             end=pd.Timestamp('2020-01-13', tz='UTC')))
    return pd.DataFrame(rows)


def test_total_cap_dedup_done_and_fixed_denominator():
    metrics, alerts = replay_policy(sample(), 'quota', 'k2')
    assert len(alerts) == 2
    assert alerts.issue_id.nunique() == 2
    assert 0 not in set(alerts.issue_id)
    assert metrics.iloc[0].positives == 2
    assert metrics.iloc[0].n_active == 5


def test_selection_is_label_and_order_independent():
    data = sample()
    _, expected = replay_policy(data, 'quota', 'k2')
    changed = data.sample(frac=1, random_state=42).copy()
    changed['y'] = 1 - changed.y
    _, actual = replay_policy(changed, 'quota', 'k2')
    assert expected[['issue_id', 'landmark']].equals(actual[['issue_id', 'landmark']])


def test_zero_cap_returns_na_recall_when_no_positive():
    data = sample()[sample().issue_id < 3].copy()
    data['y'] = 0
    metrics, alerts = replay_policy(data, 'quota', 'floor20')
    assert alerts.empty
    assert metrics.iloc[0].cap == 0
    assert pd.isna(metrics.iloc[0].recall)


def test_midpoint_can_miss_issue_completed_after_initial_landmark():
    metrics, alerts = replay_policy(sample(), 'midpoint', 'k1')
    assert list(alerts.issue_id) == [2]
    assert metrics.iloc[0].early_recall == .5


def test_all_done_keeps_sprint_with_no_alerts():
    data = sample()
    data['dynamic_is_done'] = 1
    metrics, alerts = replay_policy(data, 'quota', 'k3')
    assert metrics.iloc[0].n_active == 0
    assert metrics.iloc[0].alerts == 0
    assert alerts.empty


def test_reopened_after_initial_done_is_not_added_to_fixed_population():
    data = sample()
    data.loc[(data.issue_id == 0) & (data.landmark > .25), 'dynamic_is_done'] = 0
    _, alerts = replay_policy(data, 'late', 'k3')
    assert 0 not in set(alerts.issue_id)


@pytest.mark.parametrize('mutation', ['duplicate', 'missing', 'score', 'future', 'label', 'done'])
def test_rejects_malformed_input(mutation):
    data = sample()
    if mutation == 'duplicate':
        data = pd.concat([data, data.iloc[:1]], ignore_index=True)
    elif mutation == 'missing':
        data = data.iloc[1:]
    elif mutation == 'score':
        data.loc[0, 'p_raw'] = float('nan')
    elif mutation == 'future':
        data.loc[0, 'prediction_at'] = data.loc[0, 'end'] + pd.Timedelta(days=1)
    elif mutation == 'label':
        data.loc[0, 'y'] = 1 - data.loc[0, 'y']
    else:
        data.loc[0, 'dynamic_is_done'] = 2
    with pytest.raises(ValueError):
        replay_policy(data, 'quota', 'k2')
