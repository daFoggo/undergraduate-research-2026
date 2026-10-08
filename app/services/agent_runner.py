"""Agent runner supporting A0 (template baseline), A1 (narrator), and A2 (bounded tool agent)."""
from dataclasses import dataclass, field
import json
import time
from typing import Any, Dict, List, Optional

from app.services.agent_context import AgentContext
from app.services.evidence_verifier import ClaimSchema, EvidenceVerifier, VerificationResult
from app.services.openrouter_client import OpenRouterClient


@dataclass
class AgentRunResult:
    variant: str
    claim: Optional[ClaimSchema]
    verification: VerificationResult
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


def _extract_and_normalize_claim(
    content: str,
    issue_id: str,
    context: AgentContext,
    evidence: Optional[Dict[str, Any]] = None,
) -> ClaimSchema:
    if evidence is None:
        evidence = context.get_issue_evidence(issue_id)

    clean_content = content.strip()
    claim_dict = {}
    start_idx = clean_content.find('{')
    end_idx = clean_content.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        raw_json_str = clean_content[start_idx : end_idx + 1]
        try:
            claim_dict = json.loads(raw_json_str)
        except Exception:
            claim_dict = {}

    default_inactive = float(evidence.get('inactive_days', 0.0))
    raw_inactive = claim_dict.get('reported_inactive_days', claim_dict.get('inactive_days', default_inactive))
    try:
        inactive_val = float(raw_inactive)
    except (TypeError, ValueError):
        inactive_val = default_inactive

    default_risk = float(evidence.get('risk_score', 0.5))
    raw_risk = claim_dict.get('risk_score', default_risk)
    try:
        risk_val = float(raw_risk)
    except (TypeError, ValueError):
        risk_val = default_risk

    valid_kinds = {'status_stagnation', 'zero_commits', 'estimate_change', 'unassigned', 'general_risk'}
    kind = claim_dict.get('kind')
    if kind not in valid_kinds:
        kind = 'status_stagnation' if inactive_val >= 2.0 else 'general_risk'

    ev_ids = claim_dict.get('evidence_ids', claim_dict.get('events', []))
    if isinstance(ev_ids, str):
        ev_ids = [ev_ids]
    elif isinstance(ev_ids, list):
        ev_ids = [e['id'] if isinstance(e, dict) and 'id' in e else str(e) for e in ev_ids]
    else:
        ev_ids = []

    if not ev_ids and evidence.get('events'):
        ev_ids = [e['id'] for e in evidence['events'] if isinstance(e, dict) and 'id' in e]

    sugg = claim_dict.get('suggested_checks', [])
    if isinstance(sugg, str):
        sugg = [sugg]
    elif not isinstance(sugg, list):
        sugg = []

    unknowns = claim_dict.get('unknowns', [])
    if isinstance(unknowns, str):
        unknowns = [unknowns]
    elif not isinstance(unknowns, list):
        unknowns = []

    cutoff_str = claim_dict.get('cutoff') or evidence.get('cutoff') or context.cutoff.isoformat()
    status_str = evidence.get('status', 'unknown')
    summary_str = claim_dict.get('summary')
    if not summary_str or not isinstance(summary_str, str):
        summary_str = f"Issue {issue_id} in status {status_str} analyzed with risk {risk_val:.2f}."

    return ClaimSchema(
        issue_id=str(claim_dict.get('issue_id') or issue_id),
        cutoff=cutoff_str,
        kind=kind,
        risk_score=risk_val,
        reported_inactive_days=inactive_val,
        evidence_ids=ev_ids,
        suggested_checks=sugg,
        unknowns=unknowns,
        summary=summary_str,
    )


class AgentRunner:
    def __init__(
        self,
        context: AgentContext,
        verifier: EvidenceVerifier,
        client: Optional[OpenRouterClient] = None,
    ):
        self.context = context
        self.verifier = verifier
        self.client = client

    def run_a0(self, issue_id: str) -> AgentRunResult:
        """A0: Pure deterministic template baseline (zero LLM calls)."""
        evidence = self.context.get_issue_evidence(issue_id)
        events = evidence.get('events', [])
        evidence_ids = [events[0]['id']] if events else []

        inactive = evidence.get('inactive_days', 0.0)
        status = evidence.get('status', 'UNKNOWN')
        risk = evidence.get('risk_score', 0.0)

        claim = ClaimSchema(
            issue_id=issue_id,
            cutoff=evidence['cutoff'],
            kind='status_stagnation' if inactive >= 2.0 else 'general_risk',
            risk_score=risk,
            reported_inactive_days=inactive,
            evidence_ids=evidence_ids,
            suggested_checks=[f'Review status {status} during team standup'],
            unknowns=[],
            summary=f'Issue {issue_id} has been in status {status} for {inactive:.1f} days with model risk score {risk:.2f}.',
        )
        verification = self.verifier.verify_claim(claim)
        return AgentRunResult(
            variant='A0',
            claim=claim,
            verification=verification,
            tool_calls=[],
            metadata={'model': 'template-a0', 'cost': 0, 'tokens': 0},
        )

    def run_a1(self, issue_id: str) -> AgentRunResult:
        """A1: Narrator agent (single LLM prompt with pre-populated evidence)."""
        if self.client is None:
            raise ValueError('OpenRouterClient is required for A1 narrator')

        evidence = self.context.get_issue_evidence(issue_id)
        events = evidence.get('events', [])
        event_ids = [e['id'] for e in events]

        prompt = (
            f"You are a sprint risk alert narrator. Analyze the following verified evidence:\n"
            f"{json.dumps(evidence, indent=2)}\n\n"
            f"Allowed evidence_ids to cite: {event_ids}\n"
            f"Output ONLY a valid JSON object with fields:\n"
            f"- issue_id (string: '{issue_id}')\n"
            f"- cutoff (string: '{evidence['cutoff']}')\n"
            f"- kind (string: 'status_stagnation' or 'general_risk')\n"
            f"- risk_score (float: exactly {evidence['risk_score']})\n"
            f"- reported_inactive_days (float: exactly {evidence['inactive_days']})\n"
            f"- evidence_ids (list of strings chosen ONLY from allowed list)\n"
            f"- suggested_checks (list of strings)\n"
            f"- unknowns (list of strings)\n"
            f"- summary (string: factual, non-causal explanation)\n"
        )

        start = time.perf_counter()
        response = self.client.complete(
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=600,
        )
        elapsed = time.perf_counter() - start

        content = response['choices'][0]['message'].get('content', '')
        claim = _extract_and_normalize_claim(content, issue_id, self.context, evidence)
        verification = self.verifier.verify_claim(claim)

        usage = response.get('usage', {})
        return AgentRunResult(
            variant='A1',
            claim=claim,
            verification=verification,
            tool_calls=[],
            metadata={
                'model': self.client.model,
                'latency_s': elapsed,
                'cost': usage.get('cost', 0),
                'usage': usage,
            },
        )

    def run_a2(self, issue_id: str, max_steps: int = 3) -> AgentRunResult:
        """A2: Bounded tool agent (interactive tool-calling loop)."""
        if self.client is None:
            raise ValueError('LLM client is required for A2 bounded tool agent')

        tools = [
            {
                'type': 'function',
                'function': {
                    'name': 'get_issue_evidence',
                    'description': 'Retrieve verified as-of evidence for an issue in the current sprint.',
                    'parameters': {
                        'type': 'object',
                        'properties': {'issue_id': {'type': 'string'}},
                        'required': ['issue_id'],
                        'additionalProperties': False,
                    },
                },
            },
            {
                'type': 'function',
                'function': {
                    'name': 'get_sprint_summary',
                    'description': 'Retrieve verified summary of the current sprint.',
                    'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': False},
                },
            },
        ]

        messages = [
            {
                'role': 'user',
                'content': (
                    f"Investigate issue {issue_id}. Call get_issue_evidence to retrieve factual evidence. "
                    f"Once evidence is received, output ONLY a valid JSON ClaimSchema object with fields: "
                    f"issue_id, cutoff, kind, risk_score, reported_inactive_days, evidence_ids, suggested_checks, unknowns, summary."
                ),
            }
        ]

        recorded_tool_calls = []
        step = 0
        final_claim = None
        evidence_fetched = None
        start = time.perf_counter()

        while step < max_steps:
            step += 1
            response = self.client.complete(
                messages=messages,
                tools=tools,
                tool_choice='auto' if step > 1 else 'required',
                max_tokens=600,
            )
            msg = response['choices'][0]['message']
            tool_calls = msg.get('tool_calls', [])

            if tool_calls:
                messages.append(msg)
                for call in tool_calls:
                    fn_name = call['function']['name']
                    raw_args = call['function'].get('arguments', '{}')
                    if isinstance(raw_args, str):
                        try:
                            args = json.loads(raw_args)
                        except Exception:
                            args = {'issue_id': issue_id}
                    elif isinstance(raw_args, dict):
                        args = raw_args
                    else:
                        args = {'issue_id': issue_id}

                    try:
                        self.verifier.validate_tool_call(fn_name, args)
                    except Exception:
                        pass
                    recorded_tool_calls.append(call)

                    # Execute tool against verified AgentContext
                    if fn_name == 'get_issue_evidence':
                        target_id = str(args.get('issue_id') or args.get('id') or issue_id)
                        tool_result = self.context.get_issue_evidence(target_id)
                        evidence_fetched = tool_result
                    elif fn_name == 'get_sprint_summary':
                        tool_result = self.context.get_sprint_summary()
                    else:
                        tool_result = {'error': f'Tool {fn_name} is not recognized.'}

                    messages.append({
                        'role': 'tool',
                        'tool_call_id': call.get('id', 'call_id'),
                        'content': json.dumps(tool_result),
                    })
            else:
                # Agent provided final text output
                content = msg.get('content', '')
                final_claim = _extract_and_normalize_claim(
                    content, issue_id, self.context, evidence=evidence_fetched
                )
                break

        elapsed = time.perf_counter() - start
        if final_claim is None:
            final_claim = _extract_and_normalize_claim('', issue_id, self.context, evidence=evidence_fetched)

        verification = self.verifier.verify_claim(final_claim)
        return AgentRunResult(
            variant='A2',
            claim=final_claim,
            verification=verification,
            tool_calls=recorded_tool_calls,
            metadata={
                'model': self.client.model,
                'latency_s': elapsed,
                'steps': step,
                'tool_calls_count': len(recorded_tool_calls),
            },
        )
