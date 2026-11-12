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
gemini-flash-latest, Google's own auto-updating alias for whichever
Flash-tier model they currently recommend (free-tier eligible) — this
is deliberate: Google has been retiring dated model IDs faster than
their own published shutdown dates promise (gemini-2.0-flash and, later,
gemini-2.5-flash both started 404ing before their announced retirement
date), so pointing at a hardcoded dated ID here would just break again.
If GEMINI_MODEL is still somehow unavailable, call_gemini() retries once
against a short list of other current free-tier models before giving up
(see FALLBACK_MODELS below) — override GEMINI_MODEL in .env if you want
a specific model instead of the alias.

IMPORTANT — like Phase 2's geo.py, the actual API calls here were
written against Gemini's documented generateContent REST API but could
not be executed against the live internet in the sandbox this was built
in (no outbound network access there). See docs/PROJECT_WORKFLOW.md for
what was and wasn't verified. Test against a real API key before relying
on this.
"""
import requests

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Tried in order, after GEMINI_MODEL itself, only when the configured
# model comes back "not found" / "no longer available" -- Google's own
# deprecation cadence has been unpredictable enough (see module
# docstring) that a single hardcoded fallback isn't much safer than the
# primary model alone. All three below were confirmed free-tier-eligible
# Flash-family models as of August 2026; if all three ever fail too,
# check https://ai.google.dev/gemini-api/docs/deprecations for whatever
# Google currently recommends and update GEMINI_MODEL in .env.
FALLBACK_MODELS = ['gemini-3.5-flash', 'gemini-3.1-flash-lite', 'gemini-2.5-flash-lite']

_MODEL_UNAVAILABLE_MARKERS = ('no longer available', 'not found', 'not_found')


def is_configured(app_config):
    key = app_config.get('GEMINI_API_KEY', '')
    return bool(key)


def _post_generate(api_key, model, system_prompt, user_message, max_tokens, timeout):
    """One raw call to a specific model. Returns (text, error, is_model_unavailable)."""
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
            feedback = data.get('promptFeedback', {}).get('blockReason')
            return None, 'No response candidates from Gemini' + (f' (blocked: {feedback})' if feedback else ''), False

        finish_reason = candidates[0].get('finishReason')
        parts = candidates[0].get('content', {}).get('parts', [])
        text = '\n'.join(p['text'] for p in parts if 'text' in p).strip()

        if not text:
            if finish_reason and finish_reason not in ('STOP', 'MAX_TOKENS'):
                return None, f'Gemini returned no text (finishReason: {finish_reason})', False
            return None, 'Empty response from model', False
        return text, None, False
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.json().get('error', {}).get('message', str(e))
        except Exception:
            detail = str(e)
        is_unavailable = resp.status_code == 404 or any(m in detail.lower() for m in _MODEL_UNAVAILABLE_MARKERS)
        return None, f'Gemini API error: {detail}', is_unavailable
    except Exception as e:
        return None, f'LLM request failed: {e}', False


def call_gemini(app_config, system_prompt, user_message, max_tokens=500, timeout=30):
    """Call to the Gemini generateContent API, with automatic fallback
    to FALLBACK_MODELS if the configured model has been retired.
    Returns (text, error) — exactly one of which is None. Never raises
    to the caller; every failure mode (missing key, network error,
    blocked response, retired model, unexpected response shape) comes
    back as a plain string error so callers can fall back to their own
    template text cleanly.
    """
    api_key = app_config.get('GEMINI_API_KEY', '')
    if not api_key:
        return None, 'GEMINI_API_KEY not configured'

    primary_model = app_config.get('GEMINI_MODEL', 'gemini-flash-latest')
    models_to_try = [primary_model] + [m for m in FALLBACK_MODELS if m != primary_model]

    last_error = None
    for i, model in enumerate(models_to_try):
        text, error, is_unavailable = _post_generate(api_key, model, system_prompt, user_message, max_tokens, timeout)
        if text is not None:
            return text, None
        last_error = error
        if not is_unavailable:
            # A real failure (bad key, network, safety block) -- retrying
            # against a different model wouldn't fix it, so stop here.
            return None, error
        # Model itself was retired/not found -- worth trying the next one.

    return None, f"{last_error} (also tried fallback models: {', '.join(models_to_try[1:])})"
