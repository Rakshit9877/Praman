"""ai_core/voice.py — STUB (agent RB owns this file).

Do not implement logic here.
"""
from __future__ import annotations
from typing import Callable, Optional


async def process_voice(
    audio_path: str | None = None,
    *,
    transcript_override: str | None = None,
    progress: Optional[Callable[[str, float], None]] = None,
):
    raise NotImplementedError("voice not merged yet (agent RB)")
