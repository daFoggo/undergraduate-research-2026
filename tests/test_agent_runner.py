"""Tests for AgentRunner variants: A0 template, A1 narrator, A2 bounded tool agent."""
from datetime import datetime, timezone
import json
import httpx
import pytest

from app.services.agent_context import AgentContext
from app.services.evidence_verifier import EvidenceVerifier
from app.services.openrouter_client import OpenRouterClient
from app.services.agent_runner import AgentRunner


@pytest.fixture
def runner_setup():
    cutoff = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
    issues = {
        'PROJ-1': {
            'project': 'PROJ',
            'sprint_id': 101,
            'issue_id': 'PROJ-1',
            'status': 'IN_PROGRESS',
            'inactive_days': 5.0,
            'estimate': 8.0,
            'risk_score': 0.85,
            'events': [
                {'id': 'EVT-1', 'field': 'status', 'value': 'IN_PROGRESS', 'timestamp': '2026-03-10T10:00:00Z'},
            ],
            'description': 'Normal task description'
        }
    }
    context = AgentContext(project='PROJ', sprint_id=101, cutoff=cutoff, issues=issues)
    verifier = EvidenceVerifier(context=context)
    return context, verifier


def test_a0_template_generation(runner_setup):
    context, verifier = runner_setup
    runner = AgentRunner(context=context, verifier=verifier)
    result = runner.run_a0('PROJ-1')
    assert result.claim is not None
    assert result.claim.issue_id == 'PROJ-1'
    assert result.claim.reported_inactive_days == 5.0
    assert 'EVT-1' in result.claim.evidence_ids
    assert result.verification.valid is True


def test_a1_narrator_with_mock_client(runner_setup):
    context, verifier = runner_setup

    def mock_handler(request):
        # Return a structured claim JSON
        claim_data = {
            'issue_id': 'PROJ-1',
            'cutoff': '2026-03-15T12:00:00Z',
            'kind': 'status_stagnation',
            'risk_score': 0.85,
            'reported_inactive_days': 5.0,
            'evidence_ids': ['EVT-1'],
            'suggested_checks': ['Discuss in standup'],
            'unknowns': [],
            'summary': 'Issue PROJ-1 has been stagnant for 5.0 days.'
        }
        return httpx.Response(200, json={
            'choices': [{'message': {'role': 'assistant', 'content': json.dumps(claim_data)}, 'finish_reason': 'stop'}],
            'usage': {'cost': 0}
        })

    client = OpenRouterClient('unit-test-key', transport=httpx.MockTransport(mock_handler))
    runner = AgentRunner(context=context, verifier=verifier, client=client)
    result = runner.run_a1('PROJ-1')
    assert result.claim is not None
    assert result.claim.issue_id == 'PROJ-1'
    assert result.verification.valid is True
    assert 'unit-test-key' not in repr(result.metadata)


def test_a2_tool_agent_with_mock_client(runner_setup):
    context, verifier = runner_setup
    step = 0

    def mock_handler(request):
        nonlocal step
        step += 1
        if step == 1:
            # First step: call tool get_issue_evidence
            return httpx.Response(200, json={
                'choices': [{
                    'message': {
                        'role': 'assistant',
                        'content': None,
                        'tool_calls': [{
                            'id': 'call_1',
                            'type': 'function',
                            'function': {'name': 'get_issue_evidence', 'arguments': json.dumps({'issue_id': 'PROJ-1'})}
                        }]
                    },
                    'finish_reason': 'tool_calls'
                }],
                'usage': {'cost': 0}
            })
        else:
            # Second step: return final claim
            claim_data = {
                'issue_id': 'PROJ-1',
                'cutoff': '2026-03-15T12:00:00Z',
                'kind': 'status_stagnation',
                'risk_score': 0.85,
                'reported_inactive_days': 5.0,
                'evidence_ids': ['EVT-1'],
                'suggested_checks': ['Check dependencies'],
                'unknowns': [],
                'summary': 'PROJ-1 verified via tool: stagnant for 5.0 days.'
            }
            return httpx.Response(200, json={
                'choices': [{'message': {'role': 'assistant', 'content': json.dumps(claim_data)}, 'finish_reason': 'stop'}],
                'usage': {'cost': 0}
            })

    client = OpenRouterClient('unit-test-key', transport=httpx.MockTransport(mock_handler))
    runner = AgentRunner(context=context, verifier=verifier, client=client)
    result = runner.run_a2('PROJ-1', max_steps=3)
    assert result.claim is not None
    assert result.claim.issue_id == 'PROJ-1'
    assert result.verification.valid is True
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0]['function']['name'] == 'get_issue_evidence'
