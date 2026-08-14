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

Uses Google's Gemini API (generativelanguage.googleapis.com) rather than
a paid provider, specifically so this feature works entirely on a free
API key with no billing account required — a key from
https://aistudio.google.com/apikey starts on the free tier automatically
(see README "Getting a Gemini API key"). Default model is
gemini-2.0-flash, a free-tier model as of this writing; override via
GEMINI_MODEL if your account has access to a different free-tier model
(e.g. a newer Flash release) you'd rather use instead.

IMPORTANT — like Phase 2's geo.py, the actual API calls here were
written against Gemini's documented generateContent REST API but could
not be executed against the live internet in the sandbox this was built
in (no outbound network access there). See docs/PROJECT_WORKFLOW.md for
what was and wasn't verified. Test against a real API key before relying
on this.
"""
import requests

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def is_configured(app_config):
    key = app_config.get('GEMINI_API_KEY', '')
    return bool(key)


def call_gemini(app_config, system_prompt, user_message, max_tokens=500, timeout=30):
    """Low-level call to the Gemini generateContent API. Returns
    (text, error) — exactly one of which is None. Never raises to the
    caller; every failure mode (missing key, network error, blocked
    response, unexpected response shape) comes back as a plain string
    error so callers can fall back cleanly.
    """
    api_key = app_config.get('GEMINI_API_KEY', '')
    if not api_key:
        return None, 'GEMINI_API_KEY not configured'

    model = app_config.get('GEMINI_MODEL', 'gemini-2.0-flash')
    url = f"{GEMINI_API_BASE}/{model}:generateContent"
    headers = {
        'x-goog-api-key': api_key,
        'Content-Type': 'application/json',
    }
    payload = {
        'system_instruction': {'parts': [{'text': system_prompt}]},
        'contents': [{'role': 'user', 'parts': [{'text': user_message}]}],
        'generationConfig': {'maxOutputTokens': max_tokens},
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        candidates = data.get('candidates') or []
        if not candidates:
            # Most commonly a safety block with no candidate returned at all.
            feedback = data.get('promptFeedback', {}).get('blockReason')
            return None, 'No response candidates from Gemini' + (f' (blocked: {feedback})' if feedback else '')

        finish_reason = candidates[0].get('finishReason')
        parts = candidates[0].get('content', {}).get('parts', [])
        text = '\n'.join(p['text'] for p in parts if 'text' in p).strip()

        if not text:
            if finish_reason and finish_reason not in ('STOP', 'MAX_TOKENS'):
                return None, f'Gemini returned no text (finishReason: {finish_reason})'
            return None, 'Empty response from model'
        return text, None
    except requests.exceptions.HTTPError as e:
        # Surface the API's own error message where possible (e.g. bad
        # key, rate limit) rather than a bare status code.
        try:
            detail = resp.json().get('error', {}).get('message', str(e))
        except Exception:
            detail = str(e)
        return None, f'Gemini API error: {detail}'
    except Exception as e:
        return None, f'LLM request failed: {e}'
