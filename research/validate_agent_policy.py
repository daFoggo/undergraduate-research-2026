"""Independent output audit for E1; does not refit or edit frozen artifacts."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path('artifacts/agent_extension/policy_v1')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc_times(values):
    return pd.to_datetime(values, utc=True, format='ISO8601')


def main():
    manifest = json.loads((OUT / 'manifest.json').read_text())
    assert digest('documents/Protocol_agent_extension_v1.md') == manifest['protocol_hash']
    for path, expected in manifest['input_hashes'].items():
        assert digest(path) == expected, path
    for path, expected in manifest['source_hashes'].items():
        assert digest(path) == expected, path
    for name, expected in manifest['output_hashes'].items():
        assert digest(OUT / name) == expected, name
    metrics = pd.read_csv(OUT / 'sprint_metrics.csv')
    alerts = pd.read_csv(OUT / 'alert_log.csv')
    summary = pd.read_csv(OUT / 'summary.csv')
    ci = pd.read_csv(OUT / 'contrasts.csv')
    assert len(summary) == 96 and len(ci) == 24
    keys = ['experiment', 'model', 'capacity', 'policy', 'sprint_id']
    assert not metrics.duplicated(keys).any()
    assert not alerts.duplicated(keys + ['issue_id']).any()
    assert metrics.alerts.le(metrics.cap).all()
    counts = alerts.assign(early_tp=alerts.y.where(alerts.landmark.le(.5), 0)).groupby(keys).agg(
        observed_alerts=('y', 'size'), observed_tp=('y', 'sum'), observed_early=('early_tp', 'sum'))
    joined = metrics.set_index(keys).join(counts).fillna({'observed_alerts': 0, 'observed_tp': 0, 'observed_early': 0})
    assert joined.alerts.eq(joined.observed_alerts).all()
    assert joined.tp.eq(joined.observed_tp).all()
    assert joined.early_tp.eq(joined.observed_early).all()
    expected_early = (metrics.early_tp / metrics.positives).where(metrics.positives.gt(0))
    assert np.allclose(metrics.early_recall, expected_early, equal_nan=True)
    # Join original prefixes: all chosen issues must be open at .25 AND at selection.
    source = pd.concat([pd.read_parquet(path) for path in manifest['input_hashes']], ignore_index=True)
    source_keys = ['experiment', 'model', 'sprint_id', 'issue_id', 'landmark']
    selected = alerts.merge(source[source_keys + ['dynamic_is_done', 'y', 'p_raw', 'prediction_at', 'end']],
                            on=source_keys, validate='many_to_one', suffixes=('', '_source'))
    assert selected.dynamic_is_done.eq(0).all()
    assert selected.y.eq(selected.y_source).all()
    assert np.allclose(selected.p_raw, selected.p_raw_source)
    for field in ('prediction_at', 'end'):
        assert utc_times(selected[field]).eq(utc_times(selected[field + '_source'])).all()
    initial_keys = ['experiment', 'model', 'sprint_id', 'issue_id']
    initial = source[source.landmark.eq(.25)][initial_keys + ['dynamic_is_done']]
    active = alerts.merge(initial, on=initial_keys, validate='many_to_one')
    assert active.dynamic_is_done.eq(0).all()
    for row in summary.to_dict('records'):
        subset = metrics
        for field in ('experiment', 'model', 'capacity', 'policy'):
            subset = subset[subset[field].eq(row[field])]
        assert len(subset) == row['sprints']
        for field in ('positives', 'alerts', 'tp', 'early_tp', 'false_alerts'):
            assert subset[field].sum() == row[field]
        assert np.isclose(subset.early_recall.mean(), row['early_recall_macro_sprint'])
    result = {'status': 'pass', 'summary_rows': len(summary), 'contrasts': len(ci),
              'alerts': len(alerts), 'hashes_verified': True, 'original_prefix_eligibility': True,
              'counts_recomputed': True, 'analysis': 'posthoc_exploratory; not LLM agent validation'}
    target = OUT / 'independent_audit.json'
    # Audit report is separate from immutable experiment outputs.
    if target.exists():
        previous = json.loads(target.read_text())
        if previous != result:
            raise RuntimeError('Existing audit differs; preserve and investigate')
    else:
        target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
