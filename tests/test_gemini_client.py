"""Tests for GeminiClient."""
import httpx
import pytest

from app.services.gemini_client import GeminiClient, GeminiError


def test_repr_redacts_api_key():
    client = GeminiClient(api_key='secret-gemini-key')
    assert 'secret-gemini-key' not in repr(client)
    assert 'gemini-3.5-flash-lite' in repr(client)
    client.close()


def test_complete_single_turn_with_mock():
    def handler(request):
        return httpx.Response(200, json={
            'candidates': [{
                'content': {
                    'parts': [{'text': 'Hello from mock gemini'}]
                }
            }],
            'usageMetadata': {'promptTokenCount': 5, 'candidatesTokenCount': 4}
        })

    client = GeminiClient(api_key='test-key')
    client._client = httpx.Client(transport=httpx.MockTransport(handler))
    res = client.complete([{'role': 'user', 'content': 'Hello'}])
    assert res['choices'][0]['message']['content'] == 'Hello from mock gemini'
    assert res['usage']['cost'] == 0.0
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

    client = GeminiClient(api_key='test-key')
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
