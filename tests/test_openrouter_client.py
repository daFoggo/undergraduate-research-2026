import httpx
import pytest

from app.services.openrouter_client import OpenRouterClient, OpenRouterError


def test_pins_free_model_and_redacts_key_in_repr():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={'model': 'google/gemma-4-31b-it', 'choices': [
            {'message': {'role': 'assistant', 'content': '{}'}, 'finish_reason': 'stop'}],
            'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'cost': 0}})

    client = OpenRouterClient('unit-test-secret', transport=httpx.MockTransport(handler))
    result = client.complete([{'role': 'user', 'content': 'test'}])
    body = __import__('json').loads(requests[0].content)
    assert body['model'] == 'cohere/north-mini-code:free'
    assert body['provider']['max_price'] == {'prompt': 0, 'completion': 0}
    assert 'models' not in body
    assert result['usage']['cost'] == 0
    assert 'unit-test-secret' not in repr(client)


def test_rate_limit_reports_only_safe_metadata():
    def handler(request):
        return httpx.Response(429, headers={'Retry-After': '30'},
                              json={'error': {'message': 'unit-test-secret should not leak', 'code': 429}})
    client = OpenRouterClient('unit-test-secret', transport=httpx.MockTransport(handler))
    with pytest.raises(OpenRouterError) as caught:
        client.complete([{'role': 'user', 'content': 'test'}])
    assert caught.value.status == 429
    assert caught.value.retry_after == '30'
    assert 'unit-test-secret' not in str(caught.value)


def test_rejects_nonfree_usage_cost():
    client = OpenRouterClient('x', transport=httpx.MockTransport(lambda request: httpx.Response(
        200, json={'choices': [{'message': {'content': '{}'}, 'finish_reason': 'stop'}], 'usage': {'cost': .1}})))
    with pytest.raises(OpenRouterError, match='nonzero'):
        client.complete([{'role': 'user', 'content': 'test'}])


def test_only_explicitly_allowed_free_models_can_be_selected():
    with pytest.raises(ValueError, match='free allowlist'):
        OpenRouterClient('x', model='google/gemma-4-31b-it')
    client = OpenRouterClient('x', model='nvidia/nemotron-3-super-120b-a12b:free')
    assert client.model.endswith(':free')
    client.close()
