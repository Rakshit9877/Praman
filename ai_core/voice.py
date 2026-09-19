"""ai_core/voice.py — Hindi/Hinglish voice-note → structured VoiceClaim pipeline.

Public API
----------
    async def process_voice(
        audio_path: str | None = None,
        *,
        transcript_override: str | None = None,
        progress: ProgressCb | None = None,
    ) -> VoiceClaim

CLI (for testing without a backend):
    python -m ai_core.voice data/voice/V01.m4a
    python -m ai_core.voice --transcript "Mera naam Imran hai, carpenter hoon"
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Callable, Optional
from uuid import uuid4

from pydantic import BaseModel

from ai_core.config import settings
from ai_core.llm import LLM
from contracts.schemas import ClaimedSite, Trade, VoiceClaim

log = logging.getLogger(__name__)

# Type alias (mirrors ai_core.api.ProgressCb to avoid a circular import)
ProgressCb = Callable[[str, float], None]

# Prompt version — bump this to invalidate LLM cache when the prompt file changes.
PROMPT_VERSION = "voice_claims_v1"

_PROMPT_PATH = Path(__file__).parent / "prompts" / "voice_claims_v1.txt"


def _load_prompt() -> str:
    """Load the system prompt from the prompt file."""
    return _PROMPT_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Internal LLM output model
# (No claim_id or asr_backend — we fill those after the LLM call)
# ---------------------------------------------------------------------------

class _LLMVoiceOutput(BaseModel):
    """Schema passed to LLM.json_call; mirrors VoiceClaim fields minus metadata."""
    name: Optional[str] = None
    trade: Optional[Trade] = None
    years_experience: Optional[float] = None
    sites: list[ClaimedSite] = []
    confidence: float = 0.0


# ---------------------------------------------------------------------------
# Confidence heuristic
# ---------------------------------------------------------------------------

def _compute_confidence(result: _LLMVoiceOutput) -> float:
    """Fraction of key fields {name, trade, years_experience, >=1 site} present."""
    hits = sum([
        result.name is not None,
        result.trade is not None,
        result.years_experience is not None,
        len(result.sites) >= 1,
    ])
    return round(hits / 4.0, 2)


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

async def process_voice(
    audio_path: str | None = None,
    *,
    transcript_override: str | None = None,
    progress: ProgressCb | None = None,
) -> VoiceClaim:
    """Transcribe audio (if needed) and extract structured skill claims.

    Args:
        audio_path:          Path to the audio file (m4a / wav / mp3 / webm).
                             May be None if transcript_override is provided.
        transcript_override: Pre-supplied Hindi text. When given, ASR is skipped.
                             Use this when mic access fails or for typed input.
        progress:            Optional callback ``(stage: str, fraction: float)``.

    Returns:
        A validated VoiceClaim populated with claim_id, transcript, language,
        asr_backend, and any fields the LLM could extract from the transcript.
    """

    def _progress(stage: str, frac: float) -> None:
        if progress is not None:
            try:
                progress(stage, frac)
            except Exception:
                pass  # never let a progress callback crash the pipeline

    # ------------------------------------------------------------------
    # Step 0 — Mock mode short-circuit (AI_MODE=mock)
    # ------------------------------------------------------------------
    if settings.ai_mode == "mock":
        _progress("transcribing", 0.2)
        _progress("extracting claims", 0.7)
        from ai_core.mock import mock_process_voice  # type: ignore[import]
        result = await mock_process_voice(
            audio_path,
            transcript_override=transcript_override,
            progress=None,  # already reported above
        )
        _progress("done", 1.0)
        return result

    # ------------------------------------------------------------------
    # Step 1 — ASR (or use provided transcript)
    # ------------------------------------------------------------------
    if transcript_override is not None:
        transcript = transcript_override
        asr_backend = "override"
        log.info("process_voice: using transcript_override (skipping ASR)")
    else:
        if audio_path is None:
            raise ValueError(
                "Either audio_path or transcript_override must be provided."
            )
        _progress("transcribing", 0.2)
        from ai_core import asr
        transcript, asr_backend = asr.transcribe(audio_path)
        log.info("process_voice: ASR done (%s) → %r", asr_backend, transcript[:80])

    # ------------------------------------------------------------------
    # Step 2 — LLM extraction
    # ------------------------------------------------------------------
    _progress("extracting claims", 0.7)

    llm = LLM()

    system_prompt = _load_prompt()

    result: _LLMVoiceOutput = await llm.json_call(
        system=system_prompt,
        user_text=transcript,
        images=None,
        schema=_LLMVoiceOutput,
        prompt_version=PROMPT_VERSION,
        sample_idx=0,
        extra="voice_claims",
    )

    # ------------------------------------------------------------------
    # Step 3 — Assemble VoiceClaim
    # ------------------------------------------------------------------
    confidence = _compute_confidence(result)

    claim = VoiceClaim(
        claim_id=uuid4().hex[:12],
        transcript=transcript,
        language="hi",
        name=result.name,
        trade=result.trade,
        years_experience=result.years_experience,
        sites=result.sites,
        confidence=confidence,
        asr_backend=asr_backend,
    )

    _progress("done", 1.0)
    log.info(
        "process_voice: claim_id=%s trade=%s years=%.1f sites=%d confidence=%.2f",
        claim.claim_id,
        claim.trade,
        claim.years_experience or 0.0,
        len(claim.sites),
        claim.confidence,
    )
    return claim


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _main() -> None:
    """Command-line interface for testing the voice pipeline."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Process a voice note and print a VoiceClaim JSON."
    )
    parser.add_argument(
        "audio_path",
        nargs="?",
        default=None,
        help="Path to an audio file (m4a / wav / mp3 / webm).",
    )
    parser.add_argument(
        "--transcript",
        dest="transcript_override",
        default=None,
        help="Provide a transcript string directly (skips ASR).",
    )
    args = parser.parse_args()

    if args.audio_path is None and args.transcript_override is None:
        parser.error("Provide either audio_path or --transcript TEXT")

    def _print_progress(stage: str, frac: float) -> None:
        print(f"  [{frac:.0%}] {stage}", flush=True)

    claim = asyncio.run(
        process_voice(
            args.audio_path,
            transcript_override=args.transcript_override,
            progress=_print_progress,
        )
    )
    print(json.dumps(claim.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _main()
