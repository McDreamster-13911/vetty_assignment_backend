import time

from app.core.config import settings


_store: dict[str, tuple[float, object]] = {}


def cache_key(url: str, params: dict | None = None) -> str:
    if not params:
        return url
    query = "&".join(f"{name}={params[name]}" for name in sorted(params))
    return f"{url}?{query}"


def cache_get(url: str, params: dict | None = None):
    entry = _store.get(cache_key(url, params))
    if entry is None:
        return None
    expires_at, value = entry
    if time.monotonic() >= expires_at:
        del _store[cache_key(url, params)]
        return None
    return value


def cache_set(url: str, value, params: dict | None = None) -> None:
    expires_at = time.monotonic() + settings.cache_ttl_seconds
    _store[cache_key(url, params)] = (expires_at, value)
