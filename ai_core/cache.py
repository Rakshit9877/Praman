"""ai_core/cache.py — Content-addressed disk cache for LLM responses.

Key  : sha256 of canonical JSON of (provider, model, prompt_version, sample_idx,
       input_hash, extra).
Value: raw dict (validated JSON from the LLM).

Modes (controlled by settings.ai_cache):
  "on"           — read and write
  "off"          — bypass entirely (never reads, never writes)
  "replay-only"  — read-only; raises CacheMiss on a cache miss (for offline demo)
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from ai_core.config import settings

log = logging.getLogger(__name__)


class CacheMiss(RuntimeError):
    """Raised in replay-only mode when the requested key is not cached."""


def _cache_dir() -> Path:
    p = Path(settings.cache_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _make_key(
    provider: str,
    model: str,
    prompt_version: str,
    sample_idx: int,
    input_hash: str,
    extra: str = "",
) -> str:
    """Return a hex sha256 key for the given call parameters."""
    canonical = json.dumps(
        {
            "provider": provider,
            "model": model,
            "prompt_version": prompt_version,
            "sample_idx": sample_idx,
            "input_hash": input_hash,
            "extra": extra,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _cache_path(key: str) -> Path:
    return _cache_dir() / f"{key}.json"


def cache_get(key: str) -> dict[str, Any] | None:
    """Return cached value or None.

    In "off" mode always returns None.
    In "replay-only" mode raises CacheMiss instead of returning None.
    """
    if settings.ai_cache == "off":
        return None

    path = _cache_path(key)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            log.debug("cache hit: %s", key[:12])
            return data
        except json.JSONDecodeError:
            log.warning("corrupt cache entry, ignoring: %s", key[:12])
            return None

    # miss
    if settings.ai_cache == "replay-only":
        raise CacheMiss(
            f"AI_CACHE=replay-only but cache entry not found for key={key[:12]}…\n"
            "Run with AI_CACHE=on once to warm the cache."
        )
    return None


def cache_set(key: str, value: dict[str, Any]) -> None:
    """Write value to cache.  No-op in "off" and "replay-only" modes."""
    if settings.ai_cache in ("off", "replay-only"):
        return
    path = _cache_path(key)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    log.debug("cache write: %s", key[:12])


def compute_input_hash(*parts: bytes | str) -> str:
    """sha256 of concatenated bytes/strings — use for image content hashing."""
    h = hashlib.sha256()
    for part in parts:
        h.update(part if isinstance(part, bytes) else part.encode("utf-8"))
    return h.hexdigest()
