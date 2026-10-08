"""Tests for research/agent_evaluate.py."""
from research.agent_evaluate import evaluate_single_run
from research.agent_scenarios import load_dev_scenarios
from app.services.agent_runner import AgentRunner
from app.services.evidence_verifier import EvidenceVerifier


def test_evaluate_single_run_a0():
    scenarios = load_dev_scenarios(n=1, seed=42)
    sc = scenarios[0]
    verifier = EvidenceVerifier(sc['context'])
    runner = AgentRunner(sc['context'], verifier)
    row = evaluate_single_run(runner, sc, 'A0')

    assert row['status'] == 'completed'
    assert row['valid'] is True
    assert row['grounding_pass'] is True
    assert row['numeric_pass'] is True
    assert row['safety_pass'] is True
    assert row['latency_s'] >= 0.0
