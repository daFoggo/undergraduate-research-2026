"""As-of sprint agent context with temporal cutoff guards and cross-project isolation."""
from datetime import datetime, timezone
from typing import Any, Dict


class FutureDataLeakError(RuntimeError):
    """Raised when an event or access exceeds the as-of cutoff time."""
    pass


class CrossProjectAccessError(RuntimeError):
    """Raised when an issue belongs to a different project or does not exist."""
    pass


class AgentContext:
    def __init__(self, project: str, sprint_id: int, cutoff: datetime, issues: Dict[Any, Dict[str, Any]]):
        self.project = project
        self.sprint_id = sprint_id
        if cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=timezone.utc)
        self.cutoff = cutoff
        self.issues = {str(k): v for k, v in issues.items()}

    def _parse_ts(self, ts: str | datetime) -> datetime:
        if isinstance(ts, str):
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        else:
            dt = ts
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def validate_event_timestamp(self, ts: str | datetime) -> datetime:
        dt = self._parse_ts(ts)
        if dt > self.cutoff:
            raise FutureDataLeakError(f'Event timestamp {dt.isoformat()} is after cutoff {self.cutoff.isoformat()}')
        return dt

    def get_issue_evidence(self, issue_id: Any) -> Dict[str, Any]:
        str_id = str(issue_id)
        if str_id not in self.issues:
            raise CrossProjectAccessError(f'Issue {issue_id} not found in sprint {self.sprint_id}')
        issue = self.issues[str_id]
        if issue.get('project') != self.project:
            raise CrossProjectAccessError(f'Cross-project access forbidden: {issue_id} is in {issue.get("project")}, not {self.project}')

        as_of_events = []
        for evt in issue.get('events', []):
            try:
                self.validate_event_timestamp(evt['timestamp'])
                as_of_events.append(evt)
            except FutureDataLeakError:
                # Strictly filter out any future events beyond the cutoff
                continue

        evidence = {
            'project': self.project,
            'sprint_id': self.sprint_id,
            'issue_id': issue_id,
            'cutoff': self.cutoff.isoformat(),
            'status': issue.get('status'),
            'inactive_days': float(issue.get('inactive_days', 0.0)),
            'estimate': issue.get('estimate'),
            'risk_score': float(issue.get('risk_score', 0.0)),
            'events': as_of_events,
            'untrusted_content': True,
            'description': issue.get('description', ''),
        }
        return evidence

    def get_sprint_summary(self) -> Dict[str, Any]:
        return {
            'project': self.project,
            'sprint_id': self.sprint_id,
            'cutoff': self.cutoff.isoformat(),
            'cohort_size': len(self.issues),
            'issue_ids': list(self.issues.keys()),
        }
