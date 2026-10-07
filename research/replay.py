"""Forward-only replay. Never infer historical features from final issue values."""
from bisect import bisect_right
from dataclasses import dataclass
from datetime import datetime


DONE = frozenset({'done', 'resolved', 'closed', 'complete'})
CANCELLED = frozenset({'duplicate', 'invalid', "won't fix", 'not being considered'})
AMBIGUOUS = frozenset({'accepted', 'implemented', 'deployed', 'deployed to cloud',
                       'released to cloud', 'released to server', 'wad'})


def normalize(value):
    return str(value or '').strip().lower()


def sprint_set(value):
    if not value or not str(value).strip():
        return frozenset()
    parts = [part.strip() for part in str(value).split(',')]
    if any(not part.isdigit() for part in parts):
        raise ValueError(f'Unparseable sprint set: {value!r}')
    return frozenset(int(part) for part in parts)


@dataclass(frozen=True)
class Event:
    id: int
    at: datetime
    field: str
    before: str | None
    after: str | None
    before_text: str | None
    after_text: str | None


class Timeline:
    def __init__(self, events):
        self.events = sorted(events, key=lambda event: (event.at, event.id))
        self.times = [event.at for event in self.events]

    def before(self, at):
        return self.events[:bisect_right(self.times, at)]

    def field_before(self, field, at):
        return [event for event in self.before(at) if event.field == field]

    def status(self, at):
        events = self.field_before('status', at)
        return normalize(events[-1].after_text) if events else 'unknown'

    def membership(self, at):
        events = self.field_before('Sprint', at)
        return sprint_set(events[-1].after) if events else frozenset()

    def discontinuities(self, field, at):
        events = self.field_before(field, at)
        gaps = []
        for previous, current in zip(events, events[1:]):
            if field == 'Sprint':
                before, after = sprint_set(current.before), sprint_set(previous.after)
            else:
                before, after = normalize(current.before_text), normalize(previous.after_text)
            if before != after:
                gaps.append(current.id)
        return gaps

    def uncertain_interval(self, field, at):
        """Retrospective quality audit only; never use for prediction features."""
        events = [event for event in self.events if event.field==field]
        for previous,current in zip(events,events[1:]):
            if not previous.at <= at < current.at:
                continue
            if field=='Sprint':
                return sprint_set(previous.after) != sprint_set(current.before)
            return normalize(previous.after_text) != normalize(current.before_text)
        return False

    def features(self, created, start, end, at):
        events = self.before(at)
        statuses = [event for event in events if event.field == 'status']
        changes = [event for event in statuses if normalize(event.before_text) != normalize(event.after_text)]
        current = normalize(statuses[-1].after_text) if statuses else 'unknown'
        entered = next((event.at for event in reversed(changes)), None)
        priority = [event for event in events if event.field == 'priority']
        types = [event for event in events if event.field == 'issuetype']
        estimates = [event for event in events if event.field == 'Story Points']
        try:
            estimate = float(estimates[-1].after) if estimates and estimates[-1].after else None
        except ValueError:
            estimate = None
        days = lambda delta: delta.total_seconds() / 86400
        return {
            'age_days': days(at-created), 'duration_days': days(end-start),
            'status': current, 'is_done': int(current in DONE),
            'status_observed': int(bool(statuses)),
            'status_age_days': days(at-entered) if entered else None,
            'status_changes': len(changes), 'events_count': len(events),
            'events_in_sprint': sum(event.at >= start for event in events),
            'inactive_days': days(at-events[-1].at) if events else days(at-created),
            'assignee_changes': sum(event.field == 'assignee' for event in events),
            'priority_changes': len(priority), 'estimate_changes': len(estimates),
            'priority': normalize(priority[-1].after_text) if priority else 'unknown',
            'issue_type': normalize(types[-1].after_text) if types else 'unknown',
            'estimate': estimate,
            'feature_max_timestamp': events[-1].at.isoformat() if events else created.isoformat(),
        }
