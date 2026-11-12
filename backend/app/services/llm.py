"""
LLM service for Phase 3 (AI-1/AI-2/AI-3) — real LLM involvement, grounded
against this app's own computed numbers rather than free generation.

This is the piece the original project was missing entirely: "AI-powered"
in the README with zero actual language-model involvement anywhere. That
gap is closed here, deliberately narrowly:

  - The LLM is NEVER asked to produce a number (a %, a km figure, a kWh
    figure). Every number in a briefing/answer comes from this app's own
    ML prediction (predict.py) and SHAP explanation (xai.py) — the LLM's
    job is only to turn already-computed, already-correct structured
    data into fluent natural language, and to answer follow-up questions
    using ONLY the facts it's given.
  - Every prompt that includes real numbers explicitly instructs the
    model not to invent, adjust, or extrapolate beyond the provided
    figures — this is the RAG-style grounding pattern requested for
    Phase 3, not open-ended generation dressed up as analysis.
  - If no API key is configured, every caller falls back to a
    template-based version of the same content instead of failing —
    same fail-soft-and-label-it pattern used for weather (Phase 2) and
    the ML physics fallback (Phase 1).

IMPORTANT — like Phase 2's geo.py, the actual API calls here were
written against Anthropic's documented Messages API but could not be
executed against the live internet in the sandbox this was built in (no
outbound network access there). See docs/PROJECT_WORKFLOW.md for what
was and wasn't verified. Test against a real API key before relying on
this.
"""
import requests

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"


def is_configured(app_config):
    key = app_config.get('ANTHROPIC_API_KEY', '')
    return bool(key)


def call_claude(app_config, system_prompt, user_message, max_tokens=500, timeout=30):
    """Low-level call to the Anthropic Messages API. Returns (text, error) —
    exactly one of which is None. Never raises to the caller; every
    failure mode (missing key, network error, unexpected response shape)
    comes back as a plain string error so callers can fall back cleanly.
    """
    api_key = app_config.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        return None, 'ANTHROPIC_API_KEY not configured'

    model = app_config.get('ANTHROPIC_MODEL', 'claude-sonnet-5')
    headers = {
        'x-api-key': api_key,
        'anthropic-version': ANTHROPIC_API_VERSION,
        'content-type': 'application/json',
    }
    payload = {
        'model': model,
        'max_tokens': max_tokens,
        'system': system_prompt,
        'messages': [{'role': 'user', 'content': user_message}],
    }
    try:
        resp = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        text_blocks = [b['text'] for b in data.get('content', []) if b.get('type') == 'text']
        text = '\n'.join(text_blocks).strip()
        if not text:
            return None, 'Empty response from model'
        return text, None
    except requests.exceptions.HTTPError as e:
        # Surface the API's own error message where possible (e.g. bad
        # key, rate limit) rather than a bare status code.
        try:
            detail = resp.json().get('error', {}).get('message', str(e))
        except Exception:
            detail = str(e)
        return None, f'Anthropic API error: {detail}'
    except Exception as e:
        return None, f'LLM request failed: {e}'
