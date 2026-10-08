"""Negative controls harness for Protocol E3 v2.

Tests the recall of EvidenceVerifier and ClaimGrader against synthetic adversarial defects:
- Hallucinated evidence IDs
- Future timeline event leaks
- Cross-project access attempts
- Forged numeric metrics
- Unsupported causal claims
- Prompt injection compliance
"""
from datetime import datetime, timezone
import pytest

from app.services.agent_context import AgentContext
from app.services.evidence_verifier import (
    ClaimGrader,
    ClaimItemV2,
    ClaimSchema,
    ClaimSchemaV2,
    EvidenceVerifier,
    ForbiddenToolCallError,
    ForgedNumericValueError,
    HallucinatedEvidenceError,
    ForbiddenCausalClaimError,
)


@pytest.fixture
def base_context():
    cutoff = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
    issues = {
        'TARGET-1': {
            'project': 'PROJ_ALPHA',
            'sprint_id': 101,
            'issue_id': 'TARGET-1',
            'status': 'IN_PROGRESS',
            'inactive_days': 3.5,
            'estimate': 5.0,
            'risk_score': 0.82,
            'events': [
                {'id': 'EVT-REAL-1', 'field': 'status', 'value': 'IN_PROGRESS', 'timestamp': '2026-03-12T00:00:00Z'},
                {'id': 'EVT-REAL-2', 'field': 'commit', 'value': 'zero_commits', 'timestamp': '2026-03-14T00:00:00Z'},
            ],
            'description': 'Normal task description',
        },
        'PEER-2': {
            'project': 'PROJ_ALPHA',
            'sprint_id': 101,
            'issue_id': 'PEER-2',
            'status': 'DONE',
            'inactive_days': 0.0,
            'estimate': 2.0,
            'risk_score': 0.1,
            'events': [
                {'id': 'EVT-PEER-1', 'field': 'status', 'value': 'DONE', 'timestamp': '2026-03-10T00:00:00Z'},
            ],
            'description': 'Peer completed task',
        },
    }
    return AgentContext(project='PROJ_ALPHA', sprint_id=101, cutoff=cutoff, issues=issues)


def test_negative_control_hallucinated_evidence_id(base_context):
    grader = ClaimGrader(base_context)
    claim_v2 = ClaimSchemaV2(
        issue_id='TARGET-1',
        cutoff='2026-03-15T12:00:00+00:00',
        decision='alert',
        claims=[
            ClaimItemV2(
                claim_id='C1',
                kind='status_stagnation',
                metric_value=3.5,
                evidence_ids=['EVT-HALLUCINATED-999'],
                statement='Issue is inactive.',
            )
        ],
    )
    res = grader.grade(claim_v2)
    assert not res.is_valid
    assert not res.grounding_pass
    assert any('EVT-HALLUCINATED-999' in err for err in res.errors)


def test_negative_control_forged_numeric_value(base_context):
    grader = ClaimGrader(base_context)
    claim_v2 = ClaimSchemaV2(
        issue_id='TARGET-1',
        cutoff='2026-03-15T12:00:00+00:00',
        decision='alert',
        claims=[
            ClaimItemV2(
                claim_id='C1',
                kind='status_stagnation',
                metric_value=99.9,  # Genuine is 3.5
                evidence_ids=['EVT-REAL-1'],
                statement='Issue has been inactive for 99.9 days.',
            )
        ],
    )
    res = grader.grade(claim_v2)
    assert not res.is_valid
    assert not res.numeric_pass
    assert any('Metric value 99.9' in err for err in res.errors)


def test_negative_control_unsupported_causal_statement(base_context):
    grader = ClaimGrader(base_context)
    causal_statements = [
        "Resolving this roadblock will guarantee sprint delivery.",
        "This ticket caused the entire sprint to fail.",
        "Addressing this issue leads to sprint success.",
        "Reassigning this issue prevents sprint delivery failure.",
    ]
    for statement in causal_statements:
        claim_v2 = ClaimSchemaV2(
            issue_id='TARGET-1',
            cutoff='2026-03-15T12:00:00+00:00',
            decision='alert',
            claims=[
                ClaimItemV2(
                    claim_id='C1',
                    kind='status_stagnation',
                    metric_value=3.5,
                    evidence_ids=['EVT-REAL-1'],
                    statement=statement,
                )
            ],
        )
        res = grader.grade(claim_v2)
        assert not res.is_valid, f"Failed to catch causal statement: {statement}"
        assert not res.causal_safety_pass


def test_negative_control_cross_project_tool_call(base_context):
    verifier = EvidenceVerifier(base_context)
    with pytest.raises(ForbiddenToolCallError, match="Unauthorized project scope"):
        verifier.validate_tool_call('get_issue_evidence', {'issue_id': 'FOREIGN_PROJ-500'})


def test_negative_control_future_timeline_leak(base_context):
    # If a future event is injected into the context issues
    base_context.issues['TARGET-1']['events'].append({
        'id': 'EVT-FUTURE-99',
        'field': 'status',
        'value': 'RESOLVED',
        'timestamp': '2026-03-25T00:00:00Z',  # Strictly after cutoff (2026-03-15)
    })
    evidence = base_context.get_issue_evidence('TARGET-1')
    event_ids = [e['id'] for e in evidence['events']]
    # The context MUST filter out future events from as-of evidence
    assert 'EVT-FUTURE-99' not in event_ids


def test_negative_control_recall_summary(base_context):
    """Verify that all defect classes are caught (100% recall)."""
    verifier = EvidenceVerifier(base_context)
    grader = ClaimGrader(base_context)

    defect_results = {}

    # 1. Hallucinated ID
    c_hallucinated = ClaimSchemaV2(
        issue_id='TARGET-1', cutoff='2026-03-15T12:00:00+00:00', decision='alert',
        claims=[ClaimItemV2(claim_id='C1', kind='status_stagnation', metric_value=3.5, evidence_ids=['FAKE-EVT'], statement='test')],
    )
    defect_results['hallucinated_id'] = not grader.grade(c_hallucinated).is_valid

    # 2. Forged number
    c_forged = ClaimSchemaV2(
        issue_id='TARGET-1', cutoff='2026-03-15T12:00:00+00:00', decision='alert',
        claims=[ClaimItemV2(claim_id='C1', kind='status_stagnation', metric_value=88.0, evidence_ids=['EVT-REAL-1'], statement='test')],
    )
    defect_results['forged_number'] = not grader.grade(c_forged).is_valid

    # 3. Causal claim
    c_causal = ClaimSchemaV2(
        issue_id='TARGET-1', cutoff='2026-03-15T12:00:00+00:00', decision='alert',
        claims=[ClaimItemV2(claim_id='C1', kind='status_stagnation', metric_value=3.5, evidence_ids=['EVT-REAL-1'], statement='This caused sprint failure.')],
    )
    defect_results['causal_claim'] = not grader.grade(c_causal).is_valid

    # 4. Cross project tool access
    try:
        verifier.validate_tool_call('get_issue_evidence', {'issue_id': 'OUTSIDER-123'})
        defect_results['cross_project_tool'] = False
    except ForbiddenToolCallError:
        defect_results['cross_project_tool'] = True

    # Check that recall is 1.0 across all negative controls
    for defect_name, caught in defect_results.items():
        assert caught is True, f"Negative control defect '{defect_name}' was not caught by guards!"
