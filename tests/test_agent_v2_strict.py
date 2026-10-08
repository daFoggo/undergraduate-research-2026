"""Tests for Protocol E3 v2 strict parsing, independent ClaimGrader, and safety boundaries."""
from datetime import datetime, timezone
import json
import pytest

from app.services.agent_context import AgentContext
from app.services.evidence_verifier import (
    ClaimGrader,
    ClaimItemV2,
    ClaimSchema,
    ClaimSchemaV2,
    EvidenceVerifier,
    ForbiddenToolCallError,
    HallucinatedEvidenceError,
    ForgedNumericValueError,
    ForbiddenCausalClaimError,
)
from app.services.agent_runner import (
    AgentRunner,
    SchemaViolationError,
    parse_claim_strict,
)


@pytest.fixture
def strict_context():
    cutoff = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
    issues = {
        'ISSUE-100': {
            'project': 'PROJ',
            'sprint_id': 50,
            'issue_id': 'ISSUE-100',
            'status': 'IN_PROGRESS',
            'inactive_days': 4.5,
            'estimate': 5.0,
            'risk_score': 0.78,
            'events': [
                {'id': 'EVT-REAL-1', 'field': 'status', 'value': 'IN_PROGRESS', 'timestamp': '2026-03-11T00:00:00Z'},
            ],
            'description': 'Normal task description',
        }
    }
    return AgentContext(project='PROJ', sprint_id=50, cutoff=cutoff, issues=issues)


def test_parse_claim_strict_rejects_missing_json():
    with pytest.raises(SchemaViolationError, match="No JSON block found"):
        parse_claim_strict("I analyzed the task and it looks somewhat risky.", "ISSUE-100")


def test_parse_claim_strict_rejects_malformed_json():
    with pytest.raises(SchemaViolationError, match="Malformed JSON"):
        parse_claim_strict("{'issue_id': 'ISSUE-100', incomplete: true}", "ISSUE-100")



def test_parse_claim_strict_rejects_missing_required_fields():
    # Omits risk_score and reported_inactive_days
    bad_payload = json.dumps({
        'issue_id': 'ISSUE-100',
        'cutoff': '2026-03-15T12:00:00Z',
        'kind': 'status_stagnation',
        'summary': 'Some summary',
    })
    with pytest.raises(SchemaViolationError, match="Missing mandatory fields"):
        parse_claim_strict(bad_payload, "ISSUE-100")


def test_claim_grader_catches_hallucinated_evidence(strict_context):
    grader = ClaimGrader(strict_context)
    claim = ClaimSchema(
        issue_id='ISSUE-100',
        cutoff='2026-03-15T12:00:00Z',
        kind='status_stagnation',
        risk_score=0.78,
        reported_inactive_days=4.5,
        evidence_ids=['EVT-FAKE-999'],
        suggested_checks=['Review in standup'],
        unknowns=[],
        summary='Normal summary without causal claims.',
    )
    grade = grader.grade(claim)
    assert grade.valid is False
    assert grade.grounding_pass is False
    assert any("EVT-FAKE-999" in err for err in grade.errors)


def test_claim_grader_catches_forged_numeric_in_text(strict_context):
    grader = ClaimGrader(strict_context)
    # The actual inactive days is 4.5, but model claims 15 days in summary
    claim = ClaimSchema(
        issue_id='ISSUE-100',
        cutoff='2026-03-15T12:00:00Z',
        kind='status_stagnation',
        risk_score=0.78,
        reported_inactive_days=4.5,
        evidence_ids=['EVT-REAL-1'],
        suggested_checks=['Check task'],
        unknowns=[],
        summary='Issue has been completely inactive for 15.0 days.',
    )
    grade = grader.grade(claim)
    assert grade.valid is False
    assert grade.numeric_pass is False
    assert any("15.0 days" in err for err in grade.errors)


def test_claim_grader_catches_forbidden_causal_statement(strict_context):
    grader = ClaimGrader(strict_context)
    claim = ClaimSchema(
        issue_id='ISSUE-100',
        cutoff='2026-03-15T12:00:00Z',
        kind='status_stagnation',
        risk_score=0.78,
        reported_inactive_days=4.5,
        evidence_ids=['EVT-REAL-1'],
        suggested_checks=['Review'],
        unknowns=[],
        summary='This issue will definitely cause sprint failure due to team delay.',
    )
    grade = grader.grade(claim)
    assert grade.valid is False
    assert grade.safety_pass is False
    assert any("definitely cause" in err for err in grade.errors)


def test_claim_schema_v2_grading(strict_context):
    grader = ClaimGrader(strict_context)
    claim_v2 = ClaimSchemaV2(
        issue_id='ISSUE-100',
        cutoff='2026-03-15T12:00:00Z',
        claims=[
            ClaimItemV2(
                text='Issue has had no state updates for 4.5 days.',
                kind='status_stagnation',
                evidence_ids=['EVT-REAL-1'],
                numeric_values={'inactive_days': 4.5, 'risk_score': 0.78},
            )
        ],
        suggested_checks=['Review during morning standup'],
        unknowns=['External blockers'],
        summary='Task remains in progress with 4.5 days of recorded inactivity.',
    )
    grade = grader.grade(claim_v2)
    assert grade.valid is True
    assert grade.grounding_pass is True
    assert grade.numeric_pass is True
    assert grade.safety_pass is True
    assert len(grade.errors) == 0
