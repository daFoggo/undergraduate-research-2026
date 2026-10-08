"""Screening evaluator for candidate model capabilities."""
import json

CASES = [
    {
        'id': 'tool_call',
        'type': 'tool',
        'tool_name': 'get_issue_evidence',
        'expected_args': {'issue_id': 'DEMO-1'},
    },
    {
        'id': 'structured_alert',
        'type': 'content',
        'expected': {'decision': 'alert', 'issue_id': 'DEMO-1'},
    },
    {
        'id': 'structured_abstain',
        'type': 'content',
        'expected': {'decision': 'abstain'},
    },
]


def grade(case, message):
    if 'tool_calls' in message and message['tool_calls']:
        calls = message['tool_calls']
        if len(calls) != 1:
            return False
        call = calls[0]
        fn = call.get('function', {})
        if fn.get('name') != case.get('tool_name', 'get_issue_evidence'):
            return False
        try:
            args = json.loads(fn.get('arguments', '{}'))
            return args == case.get('expected_args')
        except (ValueError, TypeError):
            return False

    content_str = message.get('content')
    if not content_str or not isinstance(content_str, str):
        return False
    try:
        content = json.loads(content_str)
    except (ValueError, TypeError):
        return False

    if not isinstance(content, dict):
        return False

    expected = case.get('expected')
    if expected is not None:
        if content != expected:
            return False

    return True
