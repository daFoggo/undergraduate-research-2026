"""Tests for hardened GeminiClient."""
import json
import httpx
import pytest

from app.services.gemini_client import GeminiClient, GeminiError


def test_repr_redacts_api_key():
    client = GeminiClient(api_key='secret-gemini-key', model='gemini-2.5-flash')
    assert 'secret-gemini-key' not in repr(client)
    assert 'gemini-2.5-flash' in repr(client)
    client.close()


def test_complete_passes_key_in_header_and_generation_config():
    captured_request = {}

    def handler(request: httpx.Request):
        captured_request['url'] = str(request.url)
        captured_request['headers'] = dict(request.headers)
        captured_request['body'] = json.loads(request.read())
        return httpx.Response(200, json={
            'candidates': [{
                'content': {
                    'parts': [{'text': 'Hello from hardened mock gemini'}]
                }
            }],
            'usageMetadata': {'promptTokenCount': 25, 'candidatesTokenCount': 15, 'totalTokenCount': 40},
            'modelVersion': 'gemini-2.5-flash-001',
        })

    client = GeminiClient(api_key='secret-gemini-header-key', model='gemini-2.5-flash')
    client._client = httpx.Client(transport=httpx.MockTransport(handler))

    res = client.complete(
        messages=[{'role': 'user', 'content': 'Analyze sprint risk'}],
        max_tokens=450,
        temperature=0.0,
        top_p=0.95,
    )

    # 1. API key must NOT be in the query URL
    assert 'key=' not in captured_request['url']
    assert 'secret-gemini-header-key' not in captured_request['url']

    # 2. API key MUST be in headers
    assert captured_request['headers'].get('x-goog-api-key') == 'secret-gemini-header-key'

    # 3. GenerationConfig must be properly populated
    gen_config = captured_request['body'].get('generationConfig', {})
    assert gen_config.get('maxOutputTokens') == 450
    assert gen_config.get('temperature') == 0.0
    assert gen_config.get('topP') == 0.95

    # 4. Usage reporting must not hardcode cost to 0.0
    assert res['choices'][0]['message']['content'] == 'Hello from hardened mock gemini'
    assert res['usage']['cost'] is None
    assert res['usage']['prompt_tokens'] == 25
    assert res['usage']['completion_tokens'] == 15
    assert res['usage']['total_tokens'] == 40
    assert res['model_version'] == 'gemini-2.5-flash-001'
    client.close()


def test_complete_tool_call_translation_with_mock():
    def handler(request):
        return httpx.Response(200, json={
            'candidates': [{
                'content': {
                    'parts': [{
                        'functionCall': {
                            'name': 'get_issue_evidence',
                            'args': {'issue_id': 'TEST-1'}
                        }
                    }]
                }
            }],
            'usageMetadata': {'promptTokenCount': 10, 'candidatesTokenCount': 5}
        })

    client = GeminiClient(api_key='test-key', model='gemini-2.5-flash')
    client._client = httpx.Client(transport=httpx.MockTransport(handler))
    res = client.complete(
        messages=[{'role': 'user', 'content': 'Get evidence'}],
        tools=[{'type': 'function', 'function': {'name': 'get_issue_evidence', 'parameters': {}}}]
    )
    tcalls = res['choices'][0]['message'].get('tool_calls', [])
    assert len(tcalls) == 1
    assert tcalls[0]['function']['name'] == 'get_issue_evidence'
    assert tcalls[0]['function']['arguments'] == '{"issue_id": "TEST-1"}'
    client.close()


def test_list_models_with_mock():
    def handler(request: httpx.Request):
        assert request.headers.get('x-goog-api-key') == 'test-key'
        return httpx.Response(200, json={
            'models': [
                {'name': 'models/gemini-2.5-flash', 'displayName': 'Gemini 2.5 Flash'},
                {'name': 'models/gemini-2.5-pro', 'displayName': 'Gemini 2.5 Pro'},
            ]
        })

    client = GeminiClient(api_key='test-key')
    client._client = httpx.Client(transport=httpx.MockTransport(handler))
    models = client.list_models()
    assert len(models) == 2
    assert models[0]['name'] == 'models/gemini-2.5-flash'
    client.close()
