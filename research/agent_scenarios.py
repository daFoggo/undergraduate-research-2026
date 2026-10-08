"""Scenario generator for agent technical evaluation based on real archival snapshots."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

from app.services.agent_context import AgentContext


def build_scenario_from_row(row: pd.Series) -> Dict[str, Any]:
    project = str(row['project'])
    sprint_id = int(row['sprint_id'])
    issue_id = str(row['issue_id'])
    landmark = float(row['landmark'])
    pred_at = row['prediction_at']
    if isinstance(pred_at, str):
        cutoff = datetime.fromisoformat(pred_at.replace('Z', '+00:00'))
    else:
        cutoff = pred_at.to_pydatetime()
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)

    status = str(row.get('dynamic_status', 'UNKNOWN'))
    inactive = float(row.get('dynamic_inactive_days', 0.0))
    p_raw = float(row.get('p_raw', 0.5))
    y = int(row.get('y', 0))

    events = [
        {
            'id': f'EVT-{project}-{issue_id}-status',
            'field': 'status',
            'value': status,
            'timestamp': cutoff.isoformat(),
        }
    ]

    issues = {
        issue_id: {
            'project': project,
            'sprint_id': sprint_id,
            'issue_id': issue_id,
            'status': status,
            'inactive_days': inactive,
            'estimate': row.get('dynamic_estimate', 0.0),
            'risk_score': p_raw,
            'events': events,
            'description': f'Archival task {issue_id} in project {project}',
        }
    }

    context = AgentContext(project=project, sprint_id=sprint_id, cutoff=cutoff, issues=issues)
    return {
        'scenario_id': f'SCEN-{project}-{sprint_id}-{issue_id}-{landmark}',
        'project': project,
        'sprint_id': sprint_id,
        'issue_id': issue_id,
        'landmark': landmark,
        'risk_score': p_raw,
        'ground_truth_y': y,
        'context': context,
    }


def load_dev_scenarios(n: int = 10, seed: int = 20261008) -> List[Dict[str, Any]]:
    alert_path = Path('artifacts/agent_extension/policy_v1/alert_log.csv')
    snap_path = Path('data/processed/snapshots.parquet')
    if not alert_path.exists() or not snap_path.exists():
        raise FileNotFoundError('Required archival datasets missing for scenario generation')

    alerts = pd.read_csv(alert_path)
    filtered = alerts[
        (alerts.policy == 'midpoint') & (alerts.capacity == 'k2') & (alerts.model == 'dynamic_catboost')
    ].copy()
    sampled = filtered.sample(n=min(n, len(filtered)), random_state=seed)

    snaps = pd.read_parquet(
        snap_path,
        columns=[
            'project', 'sprint_id', 'issue_id', 'landmark',
            'dynamic_status', 'dynamic_inactive_days', 'dynamic_estimate',
        ],
    )
    merged = sampled.merge(snaps, on=['project', 'sprint_id', 'issue_id', 'landmark'], how='left')

    scenarios = []
    for _, row in merged.iterrows():
        scenarios.append(build_scenario_from_row(row))
    return scenarios
