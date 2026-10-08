"""Tests for research/agent_scenarios.py."""
from research.agent_scenarios import load_dev_scenarios


def test_load_dev_scenarios():
    scenarios = load_dev_scenarios(n=5, seed=42)
    assert len(scenarios) == 5
    first = scenarios[0]
    assert 'scenario_id' in first
    assert 'context' in first
    assert 'issue_id' in first
    evidence = first['context'].get_issue_evidence(first['issue_id'])
    assert evidence['issue_id'] == first['issue_id']
    assert len(evidence['events']) > 0
