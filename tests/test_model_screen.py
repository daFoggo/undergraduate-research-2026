import json

from research.openrouter_model_screen import grade, CASES


def test_grade_native_tool_arguments_not_just_name():
    case = CASES[0]
    message = {'tool_calls': [{'function': {'name': 'get_issue_evidence',
                                           'arguments': json.dumps({'issue_id': 'DEMO-1'})}}]}
    assert grade(case, message)
    message['tool_calls'][0]['function']['arguments'] = json.dumps({'issue_id': 'OTHER'})
    assert not grade(case, message)


def test_rejects_invented_blocker_and_extra_factual_fields():
    case = CASES[1]
    assert grade(case, {'content': json.dumps(case['expected'])})
    invented = case['expected'] | {'blocker': 'review delay'}
    assert not grade(case, {'content': json.dumps(invented)})
    assert not grade(case, {'content': json.dumps(case['expected'] | {'delay_days': 2})})


def test_no_action_and_invalid_json():
    assert grade(CASES[2], {'content': json.dumps(CASES[2]['expected'])})
    assert not grade(CASES[2], {'content': 'sure! {"decision":"alert"}'})
