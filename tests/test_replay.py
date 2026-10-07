from datetime import datetime, timedelta, timezone

import pytest

from research.replay import Event, Timeline, sprint_set

BASE = datetime(2020, 1, 1, tzinfo=timezone.utc)


def event(day, field, before, after, identifier=1):
    return Event(identifier, BASE+timedelta(days=day), field, before, after, before, after)


def test_set_valued_membership_and_removal():
    timeline = Timeline([event(0, 'Sprint', '', '12, 15'), event(2, 'Sprint', '12,15', '15', 2)])
    assert timeline.membership(BASE) == {12, 15}
    assert timeline.membership(BASE+timedelta(days=3)) == {15}
    with pytest.raises(ValueError):
        sprint_set('12,invalid')


def test_reopen_outcome_uses_end_state():
    timeline = Timeline([event(0, 'status', 'Open', 'Resolved'), event(3, 'status', 'Resolved', 'Reopened', 2)])
    assert timeline.status(BASE+timedelta(days=2)) == 'resolved'
    assert timeline.status(BASE+timedelta(days=4)) == 'reopened'


def test_features_invariant_to_deleted_or_changed_future():
    past = [event(0, 'status', 'Open', 'In Progress')]
    future = [event(8, 'status', 'In Progress', 'Closed', 2)]
    at = BASE+timedelta(days=5)
    arguments = (BASE-timedelta(days=10), BASE, BASE+timedelta(days=10), at)
    assert Timeline(past+future).features(*arguments) == Timeline(past).features(*arguments)
    assert Timeline(past+[event(9, 'status', 'Open', 'Resolved', 3)]).features(*arguments) == Timeline(past).features(*arguments)


def test_unknown_status_does_not_use_first_future_from_value():
    timeline = Timeline([event(8, 'status', 'Open', 'Closed')])
    assert timeline.status(BASE) == 'unknown'


def test_chain_audit_detects_missing_transitions():
    timeline = Timeline([event(0, 'status', 'Open', 'In Progress'), event(2,'status','Resolved','Closed',2)])
    assert timeline.discontinuities('status', BASE) == []
    assert timeline.discontinuities('status', BASE+timedelta(days=4)) == [2]
    assert timeline.uncertain_interval('status', BASE+timedelta(days=1))
    assert not timeline.uncertain_interval('status', BASE+timedelta(days=3))
