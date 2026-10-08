"""Run protocol-agent E1 without fitting models or calling external providers."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from research.agent_policy import replay_policy
from research.metrics import paired_bootstrap

OUT = Path('artifacts/agent_extension/policy_v1')
MODELS = ('business_rule', 'static_catboost', 'dynamic_catboost')
POLICIES = ('quota', 'midpoint', 'early', 'late')
CAPACITIES = ('k1', 'k2', 'k3', 'floor20')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def summarize(frame):
    positive = int(frame.positives.sum())
    count = int(frame.alerts.sum())
    return dict(sprints=len(frame), positive_sprints=int(frame.positives.gt(0).sum()),
                zero_cap_sprints=int(frame.cap.eq(0).sum()), active_issues=int(frame.n_active.sum()),
                positives=positive, alerts=count, tp=int(frame.tp.sum()),
                early_tp=int(frame.early_tp.sum()), false_alerts=int(frame.false_alerts.sum()),
                early_recall_macro_sprint=float(frame.early_recall.mean()),
                early_recall_macro_project=float(frame.groupby('project').early_recall.mean().mean()),
                recall_macro_sprint=float(frame.recall.mean()),
                recall_macro_project=float(frame.groupby('project').recall.mean().mean()),
                precision_macro_sprint=float(frame.precision.mean()),
                recall_micro=float(frame.tp.sum() / positive) if positive else None,
                early_recall_micro=float(frame.early_tp.sum() / positive) if positive else None,
                precision_micro=float(frame.tp.sum() / count) if count else None,
                false_alerts_per_sprint=float(frame.false_alerts.mean()),
                realized_budget_macro=float(frame.realized_budget.mean()),
                realized_budget_micro=float(count / frame.n0.sum()),
                used_cap=int(frame.alerts.sum()), allocated_cap=int(frame.cap.sum()),
                lead_days_macro_true_alert_sprints=float(frame.true_lead_days.mean()))


def main():
    if OUT.exists():
        raise RuntimeError('Preserve existing run; choose a new namespace instead of overwriting')
    protocol = Path('documents/Protocol_agent_extension_v1.md')
    paths = sorted(path for path in Path('artifacts/predictions').glob('*.parquet')
                   if any(path.stem.endswith('__' + model) for model in MODELS)
                   and any('__' + str(lm) + '__' in path.stem for lm in (.25, .5, .75)))
    if len(paths) != 252:
        raise RuntimeError(f'Expected 252 frozen input files, found {len(paths)}')
    hashes = {str(path): digest(path) for path in paths}
    manifest = dict(created_at=datetime.now(timezone.utc).isoformat(),
                    analysis='posthoc_exploratory; no LLM evaluation; no intervention effect',
                    seed=20261008, bootstrap_replicates=2000, protocol_hash=digest(protocol),
                    source_hashes={str(p): digest(p) for p in
                                   [Path(__file__), Path('research/agent_policy.py'), Path('research/metrics.py')]},
                    input_hashes=hashes, scorer='p_raw', policies=POLICIES, capacities=CAPACITIES)
    data = pd.concat([pd.read_parquet(path) for path in paths], ignore_index=True)
    summaries, all_metrics, all_alerts, contrasts = [], [], [], []
    for (experiment, model), group in data.groupby(['experiment', 'model']):
        for capacity in CAPACITIES:
            by_policy = {}
            for policy in POLICIES:
                metrics, alerts = replay_policy(group, policy, capacity)
                meta = dict(experiment=experiment, model=model, capacity=capacity, policy=policy)
                summaries.append(meta | summarize(metrics))
                all_metrics.append(metrics.assign(**meta))
                all_alerts.append(alerts.assign(**meta))
                by_policy[policy] = metrics
            left, right = by_policy['quota'], by_policy['midpoint']
            if experiment == 'cross_project':
                left = left.groupby('project').early_recall.mean().reset_index().rename(columns={'early_recall': 'recall'})
                right = right.groupby('project').early_recall.mean().reset_index().rename(columns={'early_recall': 'recall'})
                unit = 'project'
            else:
                left = left[['sprint_id', 'early_recall']].rename(columns={'early_recall': 'recall'})
                right = right[['sprint_id', 'early_recall']].rename(columns={'early_recall': 'recall'})
                unit = 'sprint_id'
            contrast = paired_bootstrap(left, right, unit=unit)
            contrasts.append(dict(experiment=experiment, model=model, capacity=capacity,
                                  left='quota', right='midpoint', metric='early_recall', unit=unit,
                                  analysis='posthoc_exploratory', **contrast))
        print(f'Completed {experiment}/{model}', flush=True)
    summary = pd.DataFrame(summaries)
    metrics = pd.concat(all_metrics, ignore_index=True)
    alerts = pd.concat(all_alerts, ignore_index=True)
    ci = pd.DataFrame(contrasts)
    keys = ['experiment', 'model', 'capacity', 'policy', 'sprint_id']
    if (metrics.alerts > metrics.cap).any() or alerts.duplicated(keys + ['issue_id']).any():
        raise AssertionError('Final capacity/dedup audit failed')
    if any(digest(path) != hashes[str(path)] for path in paths):
        raise RuntimeError('Frozen inputs changed during replay')
    OUT.mkdir(parents=True)
    for name, frame in [('summary', summary), ('sprint_metrics', metrics), ('alert_log', alerts), ('contrasts', ci)]:
        frame.to_csv(OUT / f'{name}.csv', index=False)
    report = ['# Kết quả exploratory về policy cảnh báo', '',
              'Không phải kết quả AI Agent/LLM hoặc chứng minh giảm trễ. Population là active-at-.25 trong labeled cohort.', '',
              'Raw ranking, fixed K hoặc floor(.2*n0), không tuning. Primary exploratory metric: recall phát hiện trước/tại .5.', '',
              '| Experiment | Capacity | Policy | Early recall macro | Recall cuối macro | Precision micro | Alerts |',
              '|---|---|---|---:|---:|---:|---:|']
    for row in summary[summary.model == 'dynamic_catboost'].to_dict('records'):
        macro = 'macro_project' if row['experiment'] == 'cross_project' else 'macro_sprint'
        report.append(f"| {row['experiment']} | {row['capacity']} | {row['policy']} | "
                      f"{row['early_recall_' + macro]:.4f} | {row['recall_' + macro]:.4f} | "
                      f"{row['precision_micro']:.4f} | {row['alerts']} |")
    report += ['', '## Quota trừ midpoint về early recall', '',
               '| Experiment | Capacity | Units | Delta pp | 95% CI pp |',
               '|---|---|---:|---:|---|']
    for row in ci[ci.model == 'dynamic_catboost'].to_dict('records'):
        report.append(f"| {row['experiment']} | {row['capacity']} | {row['n_units']} | "
                      f"{100 * row['delta']:.2f} | [{100 * row['ci_low']:.2f}; {100 * row['ci_high']:.2f}] |")
    report += ['', '## Giới hạn', '',
               'Test cũ đã được xem; toàn bộ là post-hoc. Không chọn policy/model deployment từ bảng này. '
               'Lead time chỉ trên true-alert sprints. Chưa có scope-removal-as-of filter, unknown labels hay human actionability. '
               'Capacity fixed K và cohort active khác nghiên cứu chính; không so trực tiếp con số macro với 53,36%. '
               'Sprints K=0 nằm trong summary; recall undefined nếu không có positives. '
               'CI marginal, không điều chỉnh multiplicity hoặc mọi phụ thuộc issue/sprint.', '',
               'Các baseline rule/static có trong summary.csv; không bỏ baseline yếu/mạnh khỏi báo cáo. '
               'Agent narrator/tool use, grounding, safety và người dùng chưa được đánh giá.']
    (OUT / 'report.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    manifest['output_hashes'] = {p.name: digest(p) for p in sorted(OUT.iterdir())}
    manifest['audit'] = dict(capacity=True, dedup=True, frozen_inputs_unchanged=True,
                             input_files=len(paths), summary_rows=len(summary), contrast_rows=len(ci),
                             alert_rows=len(alerts), sprint_metric_rows=len(metrics))
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest['audit']), flush=True)


if __name__ == '__main__':
    main()
