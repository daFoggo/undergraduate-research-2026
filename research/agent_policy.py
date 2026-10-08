"""Fixed-policy exploratory replay. Selection never receives outcome labels."""
import math

import numpy as np
import pandas as pd

from research.metrics import tie_key

LANDMARKS = (.25, .5, .75)
ALERT_COLUMNS = ['project', 'sprint_id', 'issue_id', 'landmark', 'p_raw',
                 'prediction_at', 'end', 'y', 'lead_days']


def validate(frame):
    required = set(ALERT_COLUMNS) - {'lead_days'} | {'dynamic_is_done'}
    if not required.issubset(frame.columns) or frame.empty:
        raise ValueError('Missing columns or empty replay')
    if frame[list(required)].isna().any().any():
        raise ValueError('Null required values')
    if frame.duplicated(['sprint_id', 'issue_id', 'landmark']).any():
        raise ValueError('Duplicate snapshot key')
    if not frame.landmark.isin(LANDMARKS).all():
        raise ValueError('Unsupported landmark')
    if not frame.groupby(['sprint_id', 'issue_id']).landmark.nunique().eq(3).all():
        raise ValueError('Incomplete trajectory')
    if not frame.groupby('sprint_id').project.nunique().eq(1).all():
        raise ValueError('Sprint crosses projects')
    if not frame.groupby(['sprint_id', 'issue_id']).y.nunique().eq(1).all():
        raise ValueError('Outcome changes across snapshots')
    if not frame.groupby('sprint_id').end.nunique().eq(1).all():
        raise ValueError('Sprint end changes')
    if not frame.groupby(['sprint_id', 'landmark']).prediction_at.nunique().eq(1).all():
        raise ValueError('Landmark time changes within sprint')
    if not np.isfinite(frame.p_raw.to_numpy(dtype=float)).all() or not frame.p_raw.between(0, 1).all():
        raise ValueError('Invalid risk score')
    if not frame.y.isin([0, 1]).all() or not frame.dynamic_is_done.isin([0, 1]).all():
        raise ValueError('Invalid label or eligibility')
    if (frame.prediction_at > frame.end).any():
        raise ValueError('Prediction after sprint end')
    times = frame[['sprint_id', 'landmark', 'prediction_at']].drop_duplicates().sort_values(['sprint_id', 'landmark'])
    if (times.groupby('sprint_id').prediction_at.diff().dropna() <= pd.Timedelta(0)).any():
        raise ValueError('Non-increasing landmark times')


def select_trajectory(prefixes, cap, policy):
    """Input intentionally excludes y; each landmark only sees its own prefix."""
    if 'y' in prefixes:
        raise ValueError('Outcome must not reach selector')
    alerted, selected = set(), []
    for step, landmark in enumerate(LANDMARKS, start=1):
        if policy != 'quota' and landmark != {'early': .25, 'midpoint': .5, 'late': .75}[policy]:
            continue
        quota = math.ceil(cap * step / 3) if policy == 'quota' else cap
        available = prefixes[(prefixes.landmark == landmark) & (prefixes.dynamic_is_done == 0)
                             & ~prefixes.issue_id.isin(alerted)].copy()
        available['tie'] = [tie_key(i, s) for i, s in zip(available.issue_id, available.sprint_id)]
        available = available.sort_values(['p_raw', 'tie'], ascending=[False, True])
        for row in available.head(max(0, quota - len(alerted))).to_dict('records'):
            alerted.add(row['issue_id'])
            selected.append(row)
    return selected


def replay_policy(frame, policy='quota', capacity='k2'):
    if policy not in {'quota', 'midpoint', 'early', 'late'}:
        raise ValueError('Unknown policy')
    if capacity not in {'k1', 'k2', 'k3', 'floor20'}:
        raise ValueError('Unknown capacity')
    validate(frame)
    records, logs = [], []
    for sprint_id, group in frame.groupby('sprint_id', sort=True):
        initial = group[group.landmark == .25]
        active = initial[initial.dynamic_is_done == 0]
        n0 = len(initial)
        cap = math.floor(.2 * n0) if capacity == 'floor20' else min(int(capacity[1:]), n0)
        prefixes = group[group.issue_id.isin(active.issue_id)].drop(columns=['y'])
        selected = select_trajectory(prefixes, cap, policy)
        outcomes = active.set_index('issue_id').y.to_dict()
        for row in selected:
            row['y'] = int(outcomes[row['issue_id']])
            row['lead_days'] = (row['end'] - row['prediction_at']).total_seconds() / 86400
            logs.append({key: row[key] for key in ALERT_COLUMNS})
        count = len(selected)
        tp = sum(row['y'] for row in selected)
        early_tp = sum(row['y'] for row in selected if row['landmark'] <= .5)
        positives = int(active.y.sum())
        true_leads = [row['lead_days'] for row in selected if row['y']]
        records.append(dict(project=initial.project.iloc[0], sprint_id=sprint_id,
                            n0=n0, n_active=len(active), positives=positives, cap=cap,
                            alerts=count, tp=tp, early_tp=early_tp, false_alerts=count - tp,
                            recall=tp / positives if positives else np.nan,
                            early_recall=early_tp / positives if positives else np.nan,
                            precision=tp / count if count else np.nan,
                            realized_budget=count / n0, utilization=count / cap if cap else np.nan,
                            true_lead_days=np.mean(true_leads) if true_leads else np.nan))
        if count > cap or len({row['issue_id'] for row in selected}) != count:
            raise AssertionError('Capacity/dedup invariant violated')
    return pd.DataFrame(records), pd.DataFrame(logs, columns=ALERT_COLUMNS)
