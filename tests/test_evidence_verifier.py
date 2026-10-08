"""Tests for EvidenceVerifier: hallucination prevention, numeric integrity, anti-causal claim."""
from datetime import datetime, timezone
import pytest

from app.services.agent_context import AgentContext
from app.services.evidence_verifier import (
    EvidenceVerifier,
    ClaimSchema,
    ForgedNumericValueError,
    HallucinatedEvidenceError,
    ForbiddenCausalClaimError,
    ForbiddenToolCallError,
)


@pytest.fixture
def test_setup():
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
                {'id': 'EVT-2', 'field': 'assignee', 'value': 'dev1', 'timestamp': '2026-03-12T09:00:00Z'},
            ],
            'description': 'Feature work'
        }
    }
    context = AgentContext(project='PROJ', sprint_id=101, cutoff=cutoff, issues=issues)
    verifier = EvidenceVerifier(context=context)
    return context, verifier


def test_valid_claim_passes(test_setup):
    context, verifier = test_setup
    claim = ClaimSchema(
        issue_id='PROJ-1',
        cutoff='2026-03-15T12:00:00Z',
        kind='status_stagnation',
        risk_score=0.85,
        reported_inactive_days=5.0,
        evidence_ids=['EVT-1'],
        suggested_checks=['Review current blockers in standup'],
        unknowns=['Current blocker details not in ticket'],
        summary='Issue has been in IN_PROGRESS for 5 days without updates.'
    )
    result = verifier.verify_claim(claim)
    assert result.valid is True
    assert len(result.errors) == 0


def test_hallucinated_evidence_id_rejected(test_setup):
    context, verifier = test_setup
    claim = ClaimSchema(
        issue_id='PROJ-1',
        cutoff='2026-03-15T12:00:00Z',
        kind='status_stagnation',
        risk_score=0.85,
        reported_inactive_days=5.0,
        evidence_ids=['EVT-FAKE-999'],
        suggested_checks=['Check task'],
        summary='Stagnant issue.'
    )
    with pytest.raises(HallucinatedEvidenceError):
        verifier.verify_claim(claim)


def test_forged_numeric_value_rejected(test_setup):
    context, verifier = test_setup
    claim = ClaimSchema(
        issue_id='PROJ-1',
        cutoff='2026-03-15T12:00:00Z',
        kind='status_stagnation',
        risk_score=0.85,
        reported_inactive_days=20.0,  # Actual is 5.0
        evidence_ids=['EVT-1'],
        suggested_checks=['Check task'],
        summary='Stagnant for 20 days.'
    )
    with pytest.raises(ForgedNumericValueError):
        verifier.verify_claim(claim)


def test_unsupported_causal_claim_rejected(test_setup):
    context, verifier = test_setup
    claim = ClaimSchema(
        issue_id='PROJ-1',
        cutoff='2026-03-15T12:00:00Z',
        kind='status_stagnation',
        risk_score=0.85,
        reported_inactive_days=5.0,
        evidence_ids=['EVT-1'],
        suggested_checks=['Check task'],
        summary='This issue will definitely cause sprint failure unless reallocated, guaranteed to prevent failure.'
    )
    with pytest.raises(ForbiddenCausalClaimError):
        verifier.verify_claim(claim)


def test_forbidden_tool_call_rejected(test_setup):
    context, verifier = test_setup
    with pytest.raises(ForbiddenToolCallError):
        verifier.validate_tool_call('send_email_alert', {'to': 'attacker@mail.com'})
