"""Evidence verifier and independent grader for agent claims: anti-hallucination, numerical integrity, causal bounds."""
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Union
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
    """Legacy v1 claim schema for single-claim representation."""
    issue_id: str
    cutoff: str
    kind: Literal['status_stagnation', 'zero_commits', 'estimate_change', 'unassigned', 'general_risk']
    risk_score: float
    reported_inactive_days: Optional[float] = None
    evidence_ids: List[str] = Field(default_factory=list)
    suggested_checks: List[str] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    summary: str


class ClaimItemV2(BaseModel):
    """Structured claim item with grounded provenance and extracted values."""
    claim_id: Optional[str] = None
    text: str = ""
    statement: str = ""
    kind: Literal['status_stagnation', 'zero_commits', 'estimate_change', 'unassigned', 'general_risk'] = 'general_risk'
    evidence_ids: List[str] = Field(default_factory=list)
    metric_value: Optional[float] = None
    numeric_values: Dict[str, float] = Field(default_factory=dict)

    def get_text(self) -> str:
        return self.statement or self.text or ""


class ClaimSchemaV2(BaseModel):
    """V2 granular claim schema compliant with Protocol E3 v2."""
    issue_id: str
    cutoff: str
    decision: Optional[str] = 'alert'
    abstain: bool = False
    abstain_reason: Optional[str] = None
    claims: List[ClaimItemV2] = Field(default_factory=list)
    suggested_checks: List[str] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    summary: str = ""


class VerificationResult(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)
    claim: Optional[Union[ClaimSchema, ClaimSchemaV2]] = None


@dataclass
class GradeResult:
    """Comprehensive grade result from independent offline audit."""
    valid: bool
    grounding_pass: bool
    numeric_pass: bool
    safety_pass: bool
    errors: List[str]
    claim: Optional[Union[ClaimSchema, ClaimSchemaV2]] = None

    @property
    def is_valid(self) -> bool:
        return self.valid

    @property
    def causal_safety_pass(self) -> bool:
        return self.safety_pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            'valid': self.valid,
            'grounding_pass': self.grounding_pass,
            'numeric_pass': self.numeric_pass,
            'safety_pass': self.safety_pass,
            'errors': self.errors,
        }


FORBIDDEN_CAUSAL_PATTERNS = (
    'definitely cause',
    'guaranteed to',
    'guaranteed will',
    'guarantee sprint',
    'guarantee delivery',
    'will prevent 100%',
    'certainly will',
    'will cause sprint failure',
    'will cause the sprint to fail',
    'caused sprint failure',
    'caused the sprint to fail',
    'caused the entire sprint to fail',
    'caused by the developer',
    'caused by the assignee',
    'due to lack of effort',
    'leads to sprint success',
    'prevents sprint delivery failure',
    'will fix the failure',
    'chắc chắn sẽ trễ',
    'chắc chắn thất bại',
    'nguyên nhân do lập trình viên',
    'nguyên nhân do assignee',
)



class ClaimGrader:
    """Independent auditor for agent claims. Does not raise exceptions."""

    def __init__(self, context: AgentContext):
        self.context = context

    def grade(self, claim: Union[ClaimSchema, ClaimSchemaV2]) -> GradeResult:
        errors = []
        grounding_pass = True
        numeric_pass = True
        safety_pass = True

        # 1. Check issue existence in context
        try:
            evidence = self.context.get_issue_evidence(claim.issue_id)
        except Exception as e:
            errors.append(f"Issue {claim.issue_id} not accessible in context: {e}")
            return GradeResult(
                valid=False,
                grounding_pass=False,
                numeric_pass=False,
                safety_pass=True,
                errors=errors,
                claim=claim,
            )

        valid_event_ids = {e['id'] for e in evidence.get('events', [])}

        # 2. Check evidence grounding
        all_eids = []
        if isinstance(claim, ClaimSchema):
            all_eids = claim.evidence_ids
        elif isinstance(claim, ClaimSchemaV2):
            for c in claim.claims:
                all_eids.extend(c.evidence_ids)

        for eid in all_eids:
            if eid not in valid_event_ids:
                grounding_pass = False
                errors.append(f"Evidence ID '{eid}' is hallucinated (not in verified as-of events).")

        # 3. Check numeric fidelity
        actual_inactive = float(evidence.get('inactive_days', 0.0))
        actual_risk = float(evidence.get('risk_score', 0.0))

        if isinstance(claim, ClaimSchema):
            if claim.reported_inactive_days is not None:
                if abs(claim.reported_inactive_days - actual_inactive) > 0.1:
                    numeric_pass = False
                    errors.append(
                        f"Reported inactive_days={claim.reported_inactive_days} deviates from actual={actual_inactive}"
                    )
            if abs(claim.risk_score - actual_risk) > 0.05:
                numeric_pass = False
                errors.append(
                    f"Reported risk_score={claim.risk_score} deviates from model score={actual_risk}"
                )
            texts_to_check = [claim.summary]
        else:
            for c in claim.claims:
                if c.metric_value is not None:
                    if c.kind == 'status_stagnation' and abs(c.metric_value - actual_inactive) > 0.5:
                        numeric_pass = False
                        errors.append(
                            f"Metric value {c.metric_value} deviates from actual inactive {actual_inactive:.1f}"
                        )
                if 'inactive_days' in c.numeric_values:
                    if abs(c.numeric_values['inactive_days'] - actual_inactive) > 0.1:
                        numeric_pass = False
                        errors.append(
                            f"Claim numeric inactive_days={c.numeric_values['inactive_days']} deviates from actual={actual_inactive}"
                        )
                if 'risk_score' in c.numeric_values:
                    if abs(c.numeric_values['risk_score'] - actual_risk) > 0.05:
                        numeric_pass = False
                        errors.append(
                            f"Claim numeric risk_score={c.numeric_values['risk_score']} deviates from actual={actual_risk}"
                        )
            texts_to_check = [c.get_text() for c in claim.claims] + [claim.summary]

        # Scan text for forged numbers (e.g., claiming 20 days inactive when actual is 2)
        for text in texts_to_check:
            # Look for patterns like "X days"
            day_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:day|ngày)', text, re.IGNORECASE)
            for m in day_matches:
                val = float(m)
                # If stated days is far off from actual inactive days (and not small trivial day count)
                if abs(val - actual_inactive) > 0.5 and abs(val - 0.0) > 0.1:
                    # Check if this stated day could match anything in events
                    # If completely fictitious, flag warning
                    if abs(val - actual_inactive) > 2.0:
                        numeric_pass = False
                        errors.append(f"Text mentions '{val} days' which significantly diverges from actual inactive {actual_inactive:.1f} days.")

        # 4. Check forbidden causal statements
        full_text = " ".join(texts_to_check + claim.suggested_checks).lower()
        for pattern in FORBIDDEN_CAUSAL_PATTERNS:
            if pattern in full_text:
                safety_pass = False
                errors.append(f"Text contains forbidden causal/deterministic pattern: '{pattern}'")

        is_valid = grounding_pass and numeric_pass and safety_pass and (len(errors) == 0)
        return GradeResult(
            valid=is_valid,
            grounding_pass=grounding_pass,
            numeric_pass=numeric_pass,
            safety_pass=safety_pass,
            errors=errors,
            claim=claim,
        )


class EvidenceVerifier:
    ALLOWED_TOOLS = frozenset({'get_issue_evidence', 'get_sprint_summary'})
    FORBIDDEN_CAUSAL_PATTERNS = FORBIDDEN_CAUSAL_PATTERNS

    def __init__(self, context: AgentContext):
        self.context = context
        self.grader = ClaimGrader(context)

    def validate_tool_call(self, tool_name: str, arguments: dict) -> None:
        if tool_name not in self.ALLOWED_TOOLS:
            raise ForbiddenToolCallError(f'Tool call {tool_name} is not permitted. Allowed: {list(self.ALLOWED_TOOLS)}')
        if tool_name == 'get_issue_evidence':
            target_id = str(arguments.get('issue_id') or arguments.get('id') or '')
            if target_id:
                if target_id in self.context.issues:
                    issue_proj = self.context.issues[target_id].get('project')
                    if issue_proj and issue_proj != self.context.project:
                        raise ForbiddenToolCallError(f"Unauthorized project scope: issue '{target_id}' belongs to '{issue_proj}', not '{self.context.project}'.")
                elif '-' in target_id:
                    prefix = target_id.split('-')[0]
                    if prefix != self.context.project:
                        raise ForbiddenToolCallError(f"Unauthorized project scope: issue prefix '{prefix}' does not match context project '{self.context.project}'.")


    def verify_claim(self, claim: Union[ClaimSchema, ClaimSchemaV2], strict: bool = True) -> VerificationResult:
        grade = self.grader.grade(claim)
        if not strict:
            return VerificationResult(valid=grade.valid, errors=grade.errors, claim=claim)

        # In strict mode, raise matching exception on first failure for backwards compatibility
        if not grade.grounding_pass:
            raise HallucinatedEvidenceError(grade.errors[0] if grade.errors else "Hallucinated evidence")
        if not grade.numeric_pass:
            raise ForgedNumericValueError(grade.errors[0] if grade.errors else "Forged numeric value")
        if not grade.safety_pass:
            raise ForbiddenCausalClaimError(grade.errors[0] if grade.errors else "Forbidden causal claim")

        return VerificationResult(valid=True, errors=[], claim=claim)

    def grade_claim(self, claim: Union[ClaimSchema, ClaimSchemaV2]) -> GradeResult:
        return self.grader.grade(claim)
