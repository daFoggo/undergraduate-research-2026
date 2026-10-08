"""Secret-safe, fixed free-model client. No cross-model/paid fallback."""
import os

import httpx
from dotenv import dotenv_values

MODEL = 'cohere/north-mini-code:free'
BASE_URL = 'https://openrouter.ai/api/v1'
FREE_MODELS = frozenset({MODEL, 'google/gemma-4-31b-it:free', 'google/gemma-4-26b-a4b-it:free',
                        'nvidia/nemotron-3-ultra-550b-a55b:free',
                        'nvidia/nemotron-3-super-120b-a12b:free',
                        'poolside/laguna-xs-2.1:free',
                        'thinkingmachines/inkling:free',
                        'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free',
                        'nvidia/nemotron-3.5-content-safety:free'})


class OpenRouterError(RuntimeError):
    def __init__(self, status, reason, retry_after=None, category=None):
        self.status = status
        self.retry_after = retry_after
        self.category = category
        super().__init__(f'OpenRouter status={status}: {reason}')


class OpenRouterClient:
    def __init__(self, api_key=None, transport=None, timeout=90, model=None):
        env = dotenv_values('.env')
        self.model = model or os.getenv('OPENROUTER_MODEL') or env.get('OPENROUTER_MODEL') or MODEL
        if self.model not in FREE_MODELS:
            raise ValueError('Model must be in the explicit free allowlist')
        self._key = api_key or os.getenv('OPENROUTER_API_KEY') or env.get('OPENROUTER_API_KEY')
        if not self._key:
            raise OpenRouterError(0, 'OPENROUTER_API_KEY missing')
        self._client = httpx.Client(transport=transport, timeout=timeout,
                                   headers={'Authorization': 'Bearer ' + self._key})

    def close(self):
        self._client.close()

    def _request(self, method, path, **kwargs):
        try:
            response = self._client.request(method, BASE_URL + path, **kwargs)
        except httpx.HTTPError as error:
            raise OpenRouterError(0, type(error).__name__) from None
        if response.status_code >= 400:
            # Never log response error body, request headers, or the credential.
            category = 'unknown'
            try:
                error = response.json().get('error', {})
                words = (str(error.get('message', '')) + str(error.get('metadata', {}).get('raw', ''))).lower()
                if 'upstream' in words:
                    category = 'upstream_capacity_or_rate_limit'
                elif 'daily' in words or 'per day' in words:
                    category = 'daily_quota'
                elif response.status_code == 429:
                    category = 'rate_limit_unspecified'
            except ValueError:
                pass
            raise OpenRouterError(response.status_code, 'API request rejected',
                                  response.headers.get('Retry-After'), category)
        try:
            result = response.json()
        except ValueError:
            raise OpenRouterError(response.status_code, 'Invalid response JSON') from None
        if 'error' in result:
            raise OpenRouterError(502, 'API returned error envelope')
        return result

    def capabilities(self):
        models = self._request('GET', '/models')['data']
        found = next((m for m in models if m['id'] == self.model), None)
        if found is None:
            raise OpenRouterError(404, 'Requested free model unavailable')
        if any(float(found.get('pricing', {}).get(k, -1)) != 0 for k in ('prompt', 'completion')):
            raise OpenRouterError(0, 'Requested endpoint is not free')
        return {k: found.get(k) for k in ('id', 'context_length', 'supported_parameters', 'pricing')}

    def quota(self):
        data = self._request('GET', '/key')['data']
        return {k: data.get(k) for k in ('is_free_tier', 'free_model_daily_requests')}

    def complete(self, messages, tools=None, tool_choice=None, seed=20261008, max_tokens=1200):
        payload = dict(model=self.model, messages=messages, temperature=.2, top_p=1, seed=seed,
                       max_tokens=max_tokens, stream=False,
                       reasoning={'enabled': False},
                       provider={'require_parameters': True, 'max_price': {'prompt': 0, 'completion': 0}})
        if tools:
            payload['tools'] = tools
            payload['tool_choice'] = tool_choice or 'auto'
        result = self._request('POST', '/chat/completions', json=payload)
        if result.get('usage', {}).get('cost') not in (None, 0, 0.0):
            raise OpenRouterError(0, 'Unexpected nonzero usage cost on requested free endpoint')
        if not result.get('choices'):
            raise OpenRouterError(502, 'Missing completion choices')
        return result
