"""Secret-safe, native Google Gemini client implementing the common complete interface."""
import json
import os
from typing import Any, Dict, List, Optional
import httpx
from dotenv import dotenv_values

DEFAULT_MODEL = 'gemini-3.5-flash-lite'
BASE_URL = 'https://generativelanguage.googleapis.com/v1beta'


class GeminiError(RuntimeError):
    def __init__(self, status: int, reason: str):
        self.status = status
        # Clean any accidental key leak from error message
        safe_reason = reason.replace(os.getenv('GEMINI_API_KEY', 'UNKNOWN_KEY'), '[REDACTED]')
        super().__init__(f'Gemini API status={status}: {safe_reason}')


def _clean_schema_for_gemini(schema):
    if not isinstance(schema, dict):
        return schema
    cleaned = {}
    for k, v in schema.items():
        if k in ('additionalProperties', '$schema'):
            continue
        if isinstance(v, dict):
            cleaned[k] = _clean_schema_for_gemini(v)
        elif isinstance(v, list):
            cleaned[k] = [_clean_schema_for_gemini(item) for item in v]
        else:
            cleaned[k] = v
    return cleaned


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, timeout: int = 30):
        env = dotenv_values('.env')
        self.model = model or os.getenv('GEMINI_MODEL') or env.get('GEMINI_MODEL') or DEFAULT_MODEL
        self._key = api_key or os.getenv('GEMINI_API_KEY') or env.get('GEMINI_API_KEY')
        if not self._key:
            raise GeminiError(0, 'GEMINI_API_KEY missing')
        self._client = httpx.Client(timeout=timeout)

    def close(self):
        self._client.close()

    def __repr__(self):
        return f"<GeminiClient model='{self.model}'>"

    def list_models(self) -> List[Dict[str, Any]]:
        """List available models for the authenticated API key."""
        url = f'{BASE_URL}/models'
        headers = {'x-goog-api-key': self._key}
        try:
            res = self._client.get(url, headers=headers)
        except Exception as e:
            raise GeminiError(0, f"Connection failed during list_models: {type(e).__name__}")
        if res.status_code != 200:
            raise GeminiError(res.status_code, f"Failed to list models: {res.text[:200]}")
        data = res.json()
        return data.get('models', [])

    def complete(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        max_tokens: int = 600,
        temperature: float = 0.0,
        top_p: float = 1.0,
        response_mime_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute chat completion with generation configuration and header-based authentication."""
        url = f'{BASE_URL}/models/{self.model}:generateContent'
        headers = {
            'x-goog-api-key': self._key,
            'Content-Type': 'application/json',
        }

        # Track preceding tool calls to map tool call id back to function name
        call_id_to_name = {}
        for m in messages:
            if m.get('tool_calls'):
                for c in m['tool_calls']:
                    call_id_to_name[c.get('id', '')] = c['function']['name']

        # Format contents
        contents = []
        for m in messages:
            role = m['role']
            if role == 'user':
                contents.append({'role': 'user', 'parts': [{'text': m['content']}]})
            elif role == 'assistant':
                parts = []
                if m.get('tool_calls'):
                    for c in m['tool_calls']:
                        fn = c['function']
                        args = json.loads(fn['arguments']) if isinstance(fn.get('arguments'), str) else fn.get('arguments', {})
                        fc_obj = {'name': fn['name'], 'args': args}
                        if c.get('id'):
                            fc_obj['id'] = c['id']
                        part = {'functionCall': fc_obj}
                        if c.get('thoughtSignature'):
                            part['thoughtSignature'] = c['thoughtSignature']
                        parts.append(part)
                if m.get('content'):
                    parts.append({'text': m['content']})
                if parts:
                    contents.append({'role': 'model', 'parts': parts})
            elif role == 'tool':
                tool_content = m.get('content', '{}')
                resp_obj = json.loads(tool_content) if isinstance(tool_content, str) else tool_content
                fn_name = call_id_to_name.get(m.get('tool_call_id'), 'get_issue_evidence')
                contents.append({
                    'role': 'user',
                    'parts': [{
                        'functionResponse': {
                            'name': fn_name,
                            'response': resp_obj if isinstance(resp_obj, dict) else {'result': resp_obj}
                        }
                    }]
                })

        gen_config: Dict[str, Any] = {
            'maxOutputTokens': max_tokens,
            'temperature': temperature,
            'topP': top_p,
        }
        if response_mime_type:
            gen_config['responseMimeType'] = response_mime_type

        payload: Dict[str, Any] = {
            'contents': contents,
            'generationConfig': gen_config,
        }

        if tools:
            declarations = []
            for t in tools:
                fn = t.get('function', {})
                raw_params = fn.get('parameters', {})
                params = _clean_schema_for_gemini(raw_params)
                declarations.append({
                    'name': fn['name'],
                    'description': fn.get('description', ''),
                    'parameters': params
                })
            payload['tools'] = [{'functionDeclarations': declarations}]

        max_retries = 3
        backoff = 4.0
        res = None
        for attempt in range(max_retries):
            try:
                res = self._client.post(url, headers=headers, json=payload)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise GeminiError(0, type(e).__name__) from None
                import time
                time.sleep(backoff)
                backoff *= 2
                continue

            if res.status_code == 429:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                else:
                    raise GeminiError(429, f'Rate limit exceeded after {max_retries} attempts: {res.text[:200]}')
            break

        if res.status_code != 200:
            raise GeminiError(res.status_code, f'Gemini request rejected: {res.text[:300]}')


        data = res.json()
        candidates = data.get('candidates', [])
        if not candidates:
            raise GeminiError(502, 'No candidates returned from Gemini')

        cand_content = candidates[0].get('content', {})
        parts = cand_content.get('parts', [])

        text_content = ''
        tool_calls = []
        for i, part in enumerate(parts):
            if 'text' in part:
                text_content += part['text']
            if 'functionCall' in part:
                fn = part['functionCall']
                tc = {
                    'id': fn.get('id', f'call_{i}'),
                    'type': 'function',
                    'function': {
                        'name': fn['name'],
                        'arguments': json.dumps(fn.get('args', {}))
                    }
                }
                if 'thoughtSignature' in part:
                    tc['thoughtSignature'] = part['thoughtSignature']
                tool_calls.append(tc)

        message = {
            'role': 'assistant',
            'content': text_content if text_content else None,
        }
        if tool_calls:
            message['tool_calls'] = tool_calls

        usage_meta = data.get('usageMetadata', {})
        prompt_tokens = usage_meta.get('promptTokenCount', 0)
        completion_tokens = usage_meta.get('candidatesTokenCount', 0)
        total_tokens = usage_meta.get('totalTokenCount', prompt_tokens + completion_tokens)

        return {
            'choices': [{
                'message': message,
                'finish_reason': 'tool_calls' if tool_calls else 'stop'
            }],
            'usage': {
                'cost': None,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
            },
            'model_version': data.get('modelVersion', self.model),
        }
