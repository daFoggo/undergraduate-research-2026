"""Evidence verifier for agent claims: anti-hallucination, numerical integrity, causal bounds."""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from app.services.agent_context import AgentContext


class HallucinatedEvidenceError(ValueError):
    """Raised when an agent cites evidence IDs not present in the as-of context."""
    pass


class ForgedNumericValueError(ValueError):
    """Raised when an agent fabricates or alters numeric metrics from the ground truth."""
    pass


class ForbiddenCausalClaimError(ValueError):
    """Raised when an agent makes unwarranted causal or deterministic failure claims."""
    pass


class ForbiddenToolCallError(ValueError):
    """Raised when an agent attempts to invoke unauthorized or dangerous tools."""
    pass


class ClaimSchema(BaseModel):
    issue_id: str
    cutoff: str
    kind: Literal['status_stagnation', 'zero_commits', 'estimate_change', 'unassigned', 'general_risk']
    risk_score: float
    reported_inactive_days: Optional[float] = None
    evidence_ids: List[str] = Field(default_factory=list)
    suggested_checks: List[str] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    summary: str


class VerificationResult(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)
    claim: Optional[ClaimSchema] = None


class EvidenceVerifier:
    ALLOWED_TOOLS = frozenset({'get_issue_evidence', 'get_sprint_summary'})
    FORBIDDEN_CAUSAL_PATTERNS = (
        'definitely cause',
        'guaranteed to',
        'guaranteed will',
        'will prevent 100%',
        'certainly will',
    )

    def __init__(self, context: AgentContext):
        self.context = context

    def validate_tool_call(self, tool_name: str, arguments: dict) -> None:
        if tool_name not in self.ALLOWED_TOOLS:
            raise ForbiddenToolCallError(f'Tool call {tool_name} is not permitted. Allowed: {list(self.ALLOWED_TOOLS)}')

    def verify_claim(self, claim: ClaimSchema) -> VerificationResult:
        errors = []

        # 1. Check issue exists in context
        evidence = self.context.get_issue_evidence(claim.issue_id)
        valid_event_ids = {e['id'] for e in evidence.get('events', [])}

        # 2. Check evidence grounding (no hallucinated IDs)
        for eid in claim.evidence_ids:
            if eid not in valid_event_ids:
                raise HallucinatedEvidenceError(
                    f'Evidence ID {eid} not found in verified as-of events for {claim.issue_id}'
                )

        # 3. Check numerical integrity
        if claim.reported_inactive_days is not None:
            actual_inactive = evidence.get('inactive_days', 0.0)
            if abs(claim.reported_inactive_days - actual_inactive) > 0.1:
                raise ForgedNumericValueError(
                    f'Reported inactive_days={claim.reported_inactive_days} does not match actual={actual_inactive}'
                )

        if abs(claim.risk_score - evidence.get('risk_score', 0.0)) > 0.05:
            raise ForgedNumericValueError(
                f'Reported risk_score={claim.risk_score} deviates from model score={evidence.get("risk_score")}'
            )

        # 4. Check forbidden causal patterns in summary and suggested checks
        combined_text = (claim.summary + ' ' + ' '.join(claim.suggested_checks)).lower()
        for pattern in self.FORBIDDEN_CAUSAL_PATTERNS:
            if pattern in combined_text:
                raise ForbiddenCausalClaimError(
                    f'Claim contains forbidden deterministic/causal statement: "{pattern}"'
                )

        return VerificationResult(valid=True, errors=[], claim=claim)
