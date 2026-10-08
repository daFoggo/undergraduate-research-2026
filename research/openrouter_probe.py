"""One native tool-call probe; only synthetic context, never secret output."""
import json
from datetime import datetime, timezone
from pathlib import Path

from app.services.openrouter_client import MODEL, OpenRouterClient, OpenRouterError


def main():
    client = OpenRouterClient()
    out = Path('artifacts/agent_extension/openrouter_probe.json')
    result = {'checked_at': datetime.now(timezone.utc).isoformat(), 'requested_model': MODEL,
              'status': 'not_completed'}
    try:
        result['capabilities'] = client.capabilities()
        result['quota'] = client.quota()
        tools = [{'type': 'function', 'function': {'name': 'get_issue_evidence',
                 'description': 'Read current synthetic issue evidence.',
                 'parameters': {'type': 'object', 'properties': {'issue_id': {'type': 'string'}},
                                'required': ['issue_id'], 'additionalProperties': False}}}]
        response = client.complete([{'role': 'user', 'content': 'Call get_issue_evidence for synthetic issue DEMO-1.'}],
                                   tools=tools, tool_choice='required', max_tokens=128)
        message = response['choices'][0]['message']
        calls = message.get('tool_calls', [])
        result.update(status='pass' if len(calls) == 1 and calls[0]['function']['name'] == 'get_issue_evidence'
                      and json.loads(calls[0]['function']['arguments']) == {'issue_id': 'DEMO-1'} else 'tool_probe_failed',
                      returned_model=response.get('model'), provider=response.get('provider'),
                      native_tool_calls=len(calls), finish_reason=response['choices'][0].get('finish_reason'),
                      usage=response.get('usage', {}))
    except OpenRouterError as error:
        result.update(status='provider_error', http_status=error.status, safe_error=str(error),
                      retry_after=error.retry_after, category=error.category)
    finally:
        client.close()
    out.parent.mkdir(parents=True, exist_ok=True)
    # Probe metadata, no prompts, credentials, account labels or provider error bodies.
    out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
