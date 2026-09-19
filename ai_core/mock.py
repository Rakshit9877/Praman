"""ai_core/mock.py — Mock implementations of every ai_core.api signature.

Returns schema-valid objects built from contracts/fixtures/*.json when they
exist, otherwise falls back to minimal valid inline objects so that mock mode
never crashes regardless of whether fixtures have been committed yet.

Simulates realistic latency and progress callbacks to exercise the same code
paths as real mode.
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Optional

log = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).parent.parent
_FIXTURES = _REPO_ROOT / "contracts" / "fixtures"

ProgressCb = Callable[[str, float], None]

# ---- fixture loading helpers -----------------------------------------------

def _load_fixture(name: str) -> dict | None:
    """Load a fixture JSON file, return None if missing."""
    p = _FIXTURES / name
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log.warning("mock: malformed fixture %s, using inline fallback", name)
    return None


# ---- minimal inline fallbacks -----------------------------------------------

def _minimal_register_extraction(image_path: str) -> dict:
    """Build a minimal valid RegisterExtraction dict without fixtures."""
    from contracts.schemas import Mark
    eid = str(uuid.uuid4())
    return {
        "extraction_id": eid,
        "image_id": "mock_" + eid[:8],
        "image_url": None,
        "image_width": 800,
        "image_height": 600,
        "header": {
            "site_name":       {"value": "Adarsh Nagar Site", "confidence": 0.9, "needs_confirmation": False, "alternatives": []},
            "contractor_name": {"value": "Sunil Kumar", "confidence": 0.9, "needs_confirmation": False, "alternatives": []},
            "month":           {"value": "3", "confidence": 1.0, "needs_confirmation": False, "alternatives": []},
            "year":            {"value": "2026", "confidence": 1.0, "needs_confirmation": False, "alternatives": []},
        },
        "rows": [
            {
                "row_index": 0,
                "name_raw": "Rakesh",
                "name_latin": "Rakesh",
                "name_match_score": 1.0,
                "is_target": True,
                "bbox": None,
                "cells": [
                    {"day": d, "mark": "P", "confidence": 1.0, "needs_confirmation": False, "alternatives": [], "reasons": []}
                    for d in range(1, 27)
                ] + [
                    {"day": 27, "mark": "?", "confidence": 0.5, "needs_confirmation": True, "alternatives": ["P", "A"], "reasons": ["readers_disagree"]},
                    {"day": 28, "mark": "?", "confidence": 0.5, "needs_confirmation": True, "alternatives": ["P", "A"], "reasons": ["readers_disagree"]},
                ],
                "written_total": 26.0,
                "computed_total": 26.0,
                "total_consistent": True,
            }
        ],
        "n_samples": 2,
        "models": ["mock"],
        "warnings": [],
        "elapsed_s": 2.1,
    }


def _minimal_voice_claim() -> dict:
    return {
        "claim_id": str(uuid.uuid4()),
        "transcript": "Mera naam Rakesh hai, main mason hoon, 7 saal ka experience hai.",
        "language": "hi",
        "name": "Rakesh",
        "trade": "mason",
        "years_experience": 7.0,
        "sites": [
            {
                "site_name": "Adarsh Nagar Site",
                "city": "Delhi",
                "employer_name": "Sunil Kumar",
                "approx_from_year": 2019,
                "approx_to_year": 2026,
            }
        ],
        "confidence": 0.82,
        "asr_backend": "mock",
    }


def _minimal_work_record(worker_id: str) -> dict:
    return {
        "record_id": str(uuid.uuid4()),
        "worker_id": worker_id,
        "site_name": "Adarsh Nagar Site",
        "employer_name": "Sunil Kumar",
        "city": "Delhi",
        "role": "mason",
        "period_from": "2026-03-01",
        "period_to": "2026-03-28",
        "days_worked": 26.0,
        "day_marks": {f"2026-03-{d:02d}": "P" for d in range(1, 27)},
        "evidence": "register",
        "origin": "live",
        "image_id": "mock_image",
        "cells_confirmed_by_worker": 2,
        "cells_auto_accepted": 26,
        "attestation_id": None,
        "attestation_status": None,
    }


def _minimal_reconciliation_report() -> dict:
    return {
        "verified_days": 546.0,
        "verified_sites": 5,
        "attested_sites": 1,
        "evidenced_span_years": round(546.0 / 260, 3),
        "claimed_years": 7.0,
        "flags": [],
    }


def _minimal_trust_result() -> dict:
    return {
        "score": 74,
        "level": "high",
        "breakdown": {
            "coverage": 30.33,
            "attestation": 10.0,
            "consistency": 20.0,
            "claim_alignment": 10.0,
        },
        "suggested_class": "skilled",
        "class_reason": "Trade: mason (skilled trade), verified days: 546 ≥ 500, attested sites: 1 ≥ 1.",
    }


def _minimal_wage_band(area: str) -> dict:
    wages = {"A": (1008, 827), "B": (918, 693), "C": (781, 556)}
    skilled, unskilled = wages[area]
    delta = skilled - unskilled
    return {
        "area": area,
        "suggested_class": "skilled",
        "daily_wage": float(skilled),
        "unskilled_daily_wage": float(unskilled),
        "delta_per_day": float(delta),
        "delta_pct": round(delta / unskilled * 100, 1),
        "monthly_delta_26d": float(delta * 26),
        "source": "Central sphere minimum wages, construction 2026 (mock)",
        "effective_from": "2026-04-01",
        "effective_to": "2026-09-30",
    }


# ---- progress simulation -----------------------------------------------

_REGISTER_STAGES = [
    ("preprocess", 0.05),
    ("reading 1/2", 0.35),
    ("reading 2/2", 0.70),
    ("cross-check", 0.90),
    ("done", 1.0),
]

_VOICE_STAGES = [
    ("transcribing", 0.2),
    ("extracting claims", 0.6),
    ("validating", 0.9),
    ("done", 1.0),
]


async def _simulate_progress(stages: list[tuple[str, float]], cb: ProgressCb | None) -> None:
    for stage, frac in stages:
        if cb:
            cb(stage, frac)
        await asyncio.sleep(random.uniform(0.3, 0.7))  # noqa: S311


# ---- public mock functions -------------------------------------------------

async def mock_read_register(
    image_path: str,
    *,
    target_name: str | None = None,
    progress: ProgressCb | None = None,
) -> "RegisterExtraction":  # noqa: F821
    """Mock read_register: returns a fixture or inline fallback."""
    from contracts.schemas import RegisterExtraction

    await _simulate_progress(_REGISTER_STAGES, progress)

    data = _load_fixture("register_extraction.json") or _minimal_register_extraction(image_path)
    return RegisterExtraction.model_validate(data)


async def mock_process_voice(
    audio_path: str | None = None,
    *,
    transcript_override: str | None = None,
    progress: ProgressCb | None = None,
) -> "VoiceClaim":  # noqa: F821
    """Mock process_voice."""
    from contracts.schemas import VoiceClaim

    await _simulate_progress(_VOICE_STAGES, progress)

    data = _load_fixture("voice_claim.json") or _minimal_voice_claim()
    return VoiceClaim.model_validate(data)


def mock_build_work_record(
    extraction: "RegisterExtraction",  # noqa: F821
    confirm: "ConfirmRegisterIn",  # noqa: F821
    *,
    worker_id: str,
    origin: "Origin" = None,  # noqa: F821
) -> "WorkRecord":  # noqa: F821
    """Mock build_work_record."""
    from contracts.schemas import Origin, WorkRecord

    if origin is None:
        origin = Origin.live

    data = _load_fixture("work_record.json") or _minimal_work_record(worker_id)
    record = WorkRecord.model_validate(data)
    # Patch worker_id and origin to match what was requested
    return record.model_copy(update={"worker_id": worker_id, "origin": origin})


def mock_reconcile(
    claim: "VoiceClaim | None",  # noqa: F821
    records: "list[WorkRecord]",  # noqa: F821
    extra_flags: "list[Flag] | None" = None,  # noqa: F821
) -> "ReconciliationReport":  # noqa: F821
    """Mock reconcile."""
    from contracts.schemas import ReconciliationReport

    data = _load_fixture("reconciliation_report.json") or _minimal_reconciliation_report()
    report = ReconciliationReport.model_validate(data)
    if claim and claim.years_experience:
        report = report.model_copy(update={"claimed_years": claim.years_experience})
    if extra_flags:
        report = report.model_copy(update={"flags": report.flags + extra_flags})
    return report


def mock_score_passport(
    claim: "VoiceClaim | None",  # noqa: F821
    records: "list[WorkRecord]",  # noqa: F821
    report: "ReconciliationReport",  # noqa: F821
) -> "tuple[TrustResult, dict[str, WageBand]]":  # noqa: F821
    """Mock score_passport."""
    from contracts.schemas import TrustResult, WageBand

    trust_data = _load_fixture("trust_result.json") or _minimal_trust_result()
    trust = TrustResult.model_validate(trust_data)

    wage_bands: dict = {}
    for area in ("A", "B", "C"):
        fixture_key = f"wage_band_{area.lower()}.json"
        band_data = _load_fixture(fixture_key) or _minimal_wage_band(area)
        wage_bands[area] = WageBand.model_validate(band_data)

    return trust, wage_bands
