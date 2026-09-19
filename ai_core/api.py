"""ai_core/api.py — THE ONLY MODULE THE BACKEND IMPORTS.

All five public functions dispatch to mock.py when AI_MODE=mock, or to the
real implementation modules when AI_MODE=real.  The real modules (register_reader,
voice, records, reconcile, trust) are stubs until agents RA/RB/RC land; they
will raise NotImplementedError, which is expected behaviour during the build.

DO NOT change these function signatures — backend/app/routers depend on them.
"""
from __future__ import annotations

from typing import Callable, Optional

from contracts.schemas import (
    ConfirmRegisterIn,
    Flag,
    Origin,
    ReconciliationReport,
    RegisterExtraction,
    TrustResult,
    VoiceClaim,
    WageBand,
    WorkRecord,
)
from ai_core.config import settings

ProgressCb = Callable[[str, float], None]


# ---------------------------------------------------------------------------
# read_register
# ---------------------------------------------------------------------------

async def read_register(
    image_path: str,
    *,
    target_name: str | None = None,
    progress: ProgressCb | None = None,
) -> RegisterExtraction:
    """Extract attendance data from a handwritten hazri register photo.

    Args:
        image_path: Path to the register image file.
        target_name: Worker's name to search for (improves row identification).
        progress: Optional callback ``(stage: str, fraction: float) -> None``.

    Returns:
        A validated RegisterExtraction with per-cell confidence.
    """
    if settings.ai_mode == "mock":
        from ai_core.mock import mock_read_register
        return await mock_read_register(image_path, target_name=target_name, progress=progress)

    try:
        from ai_core import register_reader  # type: ignore[import]
    except ModuleNotFoundError as exc:
        raise NotImplementedError("register_reader not merged yet") from exc

    return await register_reader.read_register(
        image_path, target_name=target_name, progress=progress
    )


# ---------------------------------------------------------------------------
# process_voice
# ---------------------------------------------------------------------------

async def process_voice(
    audio_path: str | None = None,
    *,
    transcript_override: str | None = None,
    progress: ProgressCb | None = None,
) -> VoiceClaim:
    """Transcribe audio and extract structured skill claims.

    Args:
        audio_path: Path to the audio file (m4a/wav/mp3).  Optional if
            ``transcript_override`` is provided.
        transcript_override: Pre-supplied Hindi text; skips ASR step.
        progress: Optional progress callback.

    Returns:
        A validated VoiceClaim.
    """
    if settings.ai_mode == "mock":
        from ai_core.mock import mock_process_voice
        return await mock_process_voice(
            audio_path, transcript_override=transcript_override, progress=progress
        )

    try:
        from ai_core import voice  # type: ignore[import]
    except ModuleNotFoundError as exc:
        raise NotImplementedError("voice not merged yet") from exc

    return await voice.process_voice(
        audio_path, transcript_override=transcript_override, progress=progress
    )


# ---------------------------------------------------------------------------
# build_work_record
# ---------------------------------------------------------------------------

def build_work_record(
    extraction: RegisterExtraction,
    confirm: ConfirmRegisterIn,
    *,
    worker_id: str,
    origin: Origin = Origin.live,
) -> WorkRecord:
    """Build a WorkRecord from a confirmed RegisterExtraction.

    Applies cell corrections from ``confirm``, computes days_worked, and
    sets evidence = EvidenceLevel.register.
    """
    if settings.ai_mode == "mock":
        from ai_core.mock import mock_build_work_record
        return mock_build_work_record(extraction, confirm, worker_id=worker_id, origin=origin)

    try:
        from ai_core import records  # type: ignore[import]
    except ModuleNotFoundError as exc:
        raise NotImplementedError("records not merged yet") from exc

    return records.build_work_record(extraction, confirm, worker_id=worker_id, origin=origin)


# ---------------------------------------------------------------------------
# reconcile
# ---------------------------------------------------------------------------

def reconcile(
    claim: VoiceClaim | None,
    records: list[WorkRecord],
    extra_flags: list[Flag] | None = None,
) -> ReconciliationReport:
    """Run deterministic reconciliation rules over work records.

    Detects same-day-two-sites conflicts, total mismatches, claim-vs-evidence
    gap, etc.  Deterministic — no LLM calls.
    """
    if settings.ai_mode == "mock":
        from ai_core.mock import mock_reconcile
        return mock_reconcile(claim, records, extra_flags)

    try:
        from ai_core import reconcile as reconcile_mod  # type: ignore[import]
    except ModuleNotFoundError as exc:
        raise NotImplementedError("reconcile not merged yet") from exc

    return reconcile_mod.reconcile(claim, records, extra_flags)


# ---------------------------------------------------------------------------
# score_passport
# ---------------------------------------------------------------------------

def score_passport(
    claim: VoiceClaim | None,
    records: list[WorkRecord],
    report: ReconciliationReport,
) -> tuple[TrustResult, dict[str, WageBand]]:
    """Compute trust score and wage bands.

    Deterministic.  Returns a TrustResult and a dict keyed by area ("A"/"B"/"C").
    """
    if settings.ai_mode == "mock":
        from ai_core.mock import mock_score_passport
        return mock_score_passport(claim, records, report)

    try:
        from ai_core import trust  # type: ignore[import]
    except ModuleNotFoundError as exc:
        raise NotImplementedError("trust not merged yet") from exc

    return trust.score_passport(claim, records, report)
