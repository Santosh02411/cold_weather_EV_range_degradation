"""
INFRA-3: lightweight in-memory TTL cache for weather lookups.

Why not Flask-Caching: this project's caching need is narrow (one
function, one TTL, keyed by city) and Flask-Caching pulls in its own
backend-selection complexity for something this small. A ~20-line
dict-based cache is easier to read, has zero new dependencies, and is
honest about its one real limitation: it's per-process, in-memory
state, so it does NOT share a cache across multiple worker processes
(e.g. gunicorn with >1 worker) -- each process would hit the real API
on its own first request. That's an acceptable tradeoff for a single-
process deployment; a multi-worker deployment should replace this with
a shared cache (Redis, same as the RATELIMIT_STORAGE_URI note for
Flask-Limiter) rather than assume this in-memory cache is doing
anything for it. Documented, not hidden.
"""
import time

_cache = {}


def get_or_set(key, ttl_seconds, compute_fn):
    """Return the cached value for `key` if it's younger than
    `ttl_seconds`, otherwise call `compute_fn()`, cache the result, and
    return it. `compute_fn` is only called on a cache miss/expiry, so
    it's safe to pass a function that makes a real API call."""
    now = time.time()
    entry = _cache.get(key)
    if entry is not None:
        value, cached_at = entry
        if now - cached_at < ttl_seconds:
            return value, True  # (value, was_cache_hit)

    value = compute_fn()
    _cache[key] = (value, now)
    return value, False


def clear():
    """Mainly for tests -- drop everything cached."""
    _cache.clear()


def stats():
    """Cheap visibility into cache size for the admin panel; not a
    correctness-critical function, just informational."""
    return {'cached_keys': len(_cache)}
