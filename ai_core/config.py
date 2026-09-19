"""ai_core/config.py — Centralised settings loaded from .env.

Export:
    settings  — singleton Settings instance (use everywhere in ai_core)
    get_rules()       — parsed contracts/rules.json
    get_wage_table()  — parsed contracts/wage_table.json
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):
    """All runtime configuration for ai_core, loaded from .env (or environment)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore backend/frontend vars silently
    )

    # ---- AI mode / caching ----
    ai_mode: Literal["real", "mock"] = Field("mock", alias="AI_MODE")
    ai_cache: Literal["on", "off", "replay-only"] = Field("on", alias="AI_CACHE")

    # ---- Provider + keys ----
    llm_provider: Literal["anthropic", "gemini"] = Field("anthropic", alias="LLM_PROVIDER")
    anthropic_api_key: str = Field("", alias="ANTHROPIC_API_KEY")
    gemini_api_key: str = Field("", alias="GEMINI_API_KEY")

    # ---- Model names ----
    vision_model: str = Field("claude-sonnet-4-5", alias="VISION_MODEL")
    text_model: str = Field("claude-sonnet-4-5", alias="TEXT_MODEL")

    # ---- Register reader ----
    readers: int = Field(2, alias="READERS", ge=1, le=10)

    # ---- ASR ----
    asr_backend: Literal["whisper", "gemini", "mock"] = Field("mock", alias="ASR_BACKEND")
    whisper_model: str = Field("medium", alias="WHISPER_MODEL")

    # ---- Cache dir (relative to cwd / absolute) ----
    cache_dir: str = Field(".cache/ai", alias="AI_CACHE_DIR")


# ---------- singleton ----------
settings = Settings()


# ---------- contract helpers ----------
@lru_cache(maxsize=1)
def get_rules() -> dict[str, Any]:
    """Load contracts/rules.json once."""
    path = _REPO_ROOT / "contracts" / "rules.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def get_wage_table() -> dict[str, Any]:
    """Load contracts/wage_table.json once."""
    path = _REPO_ROOT / "contracts" / "wage_table.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)
