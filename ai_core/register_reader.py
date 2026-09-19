"""ai_core/register_reader.py — Uncertainty-aware handwritten register reader.

Entry point:
    async def read_register(image_path, *, target_name, progress, n_samples)
        -> RegisterExtraction

Internal raw schema (RawReading / RawRow / RawCell) is defined here and
is NOT exported to contracts/schemas.py.

__main__ block provides a CLI:
    python -m ai_core.register_reader path.jpg [--target "राकेश"]
"""
from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Callable, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from contracts.schemas import RegisterExtraction
from ai_core.config import settings
from ai_core.image_prep import prepare

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt version constant — bump this to invalidate the LLM cache when prompts change.
# ---------------------------------------------------------------------------
PROMPT_VERSION = "v1.0"

# ---------------------------------------------------------------------------
# Prompt files (relative to this file's parent directory)
# ---------------------------------------------------------------------------
_PROMPT_DIR = Path(__file__).parent / "prompts"
_PROMPT_FILES = ["register_v1.txt", "register_v2.txt", "register_v3.txt"]

ProgressCb = Callable[[str, float], None]


def _load_prompt(filename: str) -> str:
    """Read a prompt file from the prompts directory."""
    return (_PROMPT_DIR / filename).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Internal raw-reading schema  (NOT in contracts/schemas.py)
# ---------------------------------------------------------------------------

class RawCell(BaseModel):
    """A single attendance cell from one LLM reading."""
    day: int = Field(ge=1, le=31)
    mark: str = "?"          # "P" | "A" | "H" | "?"
    alt: Optional[str] = None


class RawRow(BaseModel):
    """One worker row from one LLM reading."""
    name_raw: str
    name_latin: Optional[str] = None
    bbox: Optional[list[float]] = None
    cells: list[RawCell] = []
    written_total: Optional[float] = None


class RawHeader(BaseModel):
    site_name: Optional[str] = None
    contractor_name: Optional[str] = None
    month: Optional[str] = None   # "1"–"12"
    year: Optional[str] = None


class RawReading(BaseModel):
    """Full output of one LLM reading of the register image."""
    header: RawHeader = Field(default_factory=RawHeader)
    rows: list[RawRow] = []


# ---------------------------------------------------------------------------
# Convert RawReading to a plain dict for aggregate.py
# ---------------------------------------------------------------------------

def _to_raw_dict(reading: RawReading) -> dict:
    """Serialise a RawReading to the dict shape aggregate.py expects."""
    return {
        "header": {
            "site_name": reading.header.site_name,
            "contractor_name": reading.header.contractor_name,
            "month": reading.header.month,
            "year": reading.header.year,
        },
        "rows": [
            {
                "name_raw": row.name_raw,
                "name_latin": row.name_latin,
                "bbox": row.bbox,
                "cells": [
                    {"day": c.day, "mark": c.mark, "alt": c.alt}
                    for c in row.cells
                ],
                "written_total": row.written_total,
            }
            for row in reading.rows
        ],
    }


# ---------------------------------------------------------------------------
# One LLM reading
# ---------------------------------------------------------------------------

async def _single_reading(
    *,
    image_bytes: bytes,
    prompt_text: str,
    prompt_version_tag: str,
    sample_idx: int,
    model: str,
) -> RawReading:
    """Run one LLM call and return a validated RawReading."""
    from ai_core.llm import LLM

    llm = LLM()
    temperature = 0.0 if sample_idx == 0 else 0.7

    return await llm.json_call(
        system=prompt_text,
        user_text=(
            "Transcribe this register page into JSON exactly as described in your instructions."
        ),
        images=[image_bytes],
        schema=RawReading,
        model=model,
        temperature=temperature,
        prompt_version=prompt_version_tag,
        sample_idx=sample_idx,
    )


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

async def read_register(
    image_path: str,
    *,
    target_name: Optional[str] = None,
    progress: Optional[ProgressCb] = None,
    n_samples: Optional[int] = None,
) -> RegisterExtraction:
    """Read a handwritten register photo and return a RegisterExtraction.

    Steps
    -----
    1. Preprocess the image (EXIF, resize, JPEG).
    2. Run *n_samples* LLM readings CONCURRENTLY using cycling prompt variants.
    3. Aggregate readings using aggregate.py (agreement-based confidence).
    4. Return a schema-valid RegisterExtraction.

    Parameters
    ----------
    image_path:
        Path to the register photo (any format Pillow can read).
    target_name:
        Worker name to fuzzy-match against rows.  If provided, the best-
        matching row gets is_target=True.
    progress:
        Optional callback (stage: str, fraction: float) for job progress.
    n_samples:
        Number of independent LLM readings.  Defaults to settings.readers.
    """
    from ai_core.aggregate import aggregate_readings

    def _prog(stage: str, frac: float) -> None:
        if progress:
            try:
                progress(stage, frac)
            except Exception:
                pass

    t_start = time.perf_counter()
    n = n_samples if n_samples is not None else settings.readers
    model = settings.vision_model

    # 1. Pre-process image ---------------------------------------------------
    _prog("preprocess", 0.05)
    prepared = prepare(image_path)
    log.info("image prepared: id=%s w=%d h=%d size=%d bytes",
             prepared.image_id, prepared.width, prepared.height,
             len(prepared.bytes_jpeg))

    # Load prompts (cycle through the three variants)
    prompts = [_load_prompt(f) for f in _PROMPT_FILES]

    # 2. Run readings concurrently -------------------------------------------
    tasks: list[asyncio.Task] = []
    loop = asyncio.get_event_loop()

    completed_count = 0
    results: list[Optional[RawReading]] = [None] * n

    async def _do_reading(idx: int, prompt_text: str) -> None:
        nonlocal completed_count
        try:
            reading = await _single_reading(
                image_bytes=prepared.bytes_jpeg,
                prompt_text=prompt_text,
                prompt_version_tag=f"{PROMPT_VERSION}-{_PROMPT_FILES[idx % len(_PROMPT_FILES)]}",
                sample_idx=idx,
                model=model,
            )
            results[idx] = reading
        except Exception as exc:
            log.warning("reading %d failed: %s", idx, exc)
            results[idx] = None
        finally:
            completed_count += 1
            _prog(f"reading {completed_count}/{n}", 0.1 + 0.7 * completed_count / n)

    coros = [
        _do_reading(i, prompts[i % len(prompts)])
        for i in range(n)
    ]
    await asyncio.gather(*coros)

    _prog("cross-check", 0.9)

    # 3. Aggregate -----------------------------------------------------------
    raw_dicts = [_to_raw_dict(r) for r in results if r is not None]
    warnings: list[str] = []

    if len(raw_dicts) < 2:
        raise ValueError(
            f"Only {len(raw_dicts)} valid reading(s) out of {n} succeeded. "
            "Need at least 2 to aggregate. Check LLM connectivity and prompt schema."
        )

    header, rows, agg_warnings = aggregate_readings(
        raw_dicts,
        target_name=target_name,
        n_valid_min=2,
    )
    warnings.extend(agg_warnings)

    elapsed = time.perf_counter() - t_start
    _prog("done", 1.0)

    extraction = RegisterExtraction(
        extraction_id=uuid4().hex[:12],
        image_id=prepared.image_id,
        image_url=None,  # filled by backend
        image_width=prepared.width,
        image_height=prepared.height,
        header=header,
        rows=rows,
        n_samples=n,
        models=[model],
        warnings=warnings,
        elapsed_s=round(elapsed, 2),
    )
    return extraction


# ---------------------------------------------------------------------------
# CLI  (python -m ai_core.register_reader path.jpg [--target NAME])
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import json
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Read a handwritten attendance register and produce a RegisterExtraction."
    )
    parser.add_argument("image", help="Path to the register photo")
    parser.add_argument(
        "--target", default=None,
        help="Worker name to match (e.g. 'राकेश' or 'Rakesh')"
    )
    parser.add_argument(
        "--n-samples", type=int, default=None,
        help="Number of LLM readings (default: settings.READERS)"
    )
    args = parser.parse_args()

    def _show_progress(stage: str, frac: float) -> None:
        bar = "#" * int(frac * 30)
        print(f"\r[{bar:<30}] {frac:4.0%}  {stage}", end="", flush=True)

    async def _main() -> None:
        extraction = await read_register(
            args.image,
            target_name=args.target,
            progress=_show_progress,
            n_samples=args.n_samples,
        )
        print()  # newline after progress bar

        # Pretty-print the full extraction
        print(extraction.model_dump_json(indent=2))

        # Human-readable table of flagged cells
        flagged = [
            (row.row_index, row.name_raw, cell.day, cell.mark.value,
             round(cell.confidence, 2), cell.reasons)
            for row in extraction.rows
            for cell in row.cells
            if cell.needs_confirmation
        ]
        if flagged:
            print("\n=== Cells needing confirmation ===")
            print(f"{'row':>4}  {'name':<20}  {'day':>4}  {'mark':>4}  {'conf':>5}  reasons")
            print("-" * 60)
            for row_i, name, day, mark, conf, reasons in flagged:
                print(f"{row_i:>4}  {name:<20}  {day:>4}  {mark:>4}  {conf:>5.2f}  {', '.join(reasons)}")
        else:
            print("\n✓ No cells need confirmation (all readings agree).")

        if extraction.warnings:
            print("\n=== Warnings ===")
            for w in extraction.warnings:
                print(f"  • {w}")

    asyncio.run(_main())
