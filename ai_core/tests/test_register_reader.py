"""ai_core/tests/test_register_reader.py — Tests for register_reader.py.

All tests here run offline (AI_MODE=mock).  The LLM call is patched to return
canned RawReading JSON so no network is required.

Run with:
    PYTHONPATH=. pytest -q -m "not live" ai_core/tests/test_register_reader.py

Live test (requires ANTHROPIC_API_KEY and AI_MODE=real):
    PYTHONPATH=. AI_MODE=real pytest -q -m "live" ai_core/tests/test_register_reader.py
"""
from __future__ import annotations

import asyncio
import io
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import pytest

from contracts.schemas import RegisterExtraction, Mark


# ---------------------------------------------------------------------------
# Canned raw reading — used to mock the LLM response
# ---------------------------------------------------------------------------

_CANNED_READING = {
    "header": {
        "site_name": "Sunrise Towers",
        "contractor_name": "Sunil Thekedar",
        "month": "9",
        "year": "2026",
    },
    "rows": [
        {
            "name_raw": "राकेश",
            "name_latin": "Rakesh",
            "bbox": [0.05, 0.2, 0.95, 0.3],
            "cells": [
                {"day": 1, "mark": "P", "alt": None},
                {"day": 2, "mark": "P", "alt": None},
                {"day": 3, "mark": "A", "alt": None},
                {"day": 4, "mark": "H", "alt": None},
                {"day": 5, "mark": "P", "alt": None},
            ],
            "written_total": 3.5,
        },
        {
            "name_raw": "सुरेश",
            "name_latin": "Suresh",
            "bbox": [0.05, 0.31, 0.95, 0.41],
            "cells": [
                {"day": 1, "mark": "A", "alt": None},
                {"day": 2, "mark": "A", "alt": None},
                {"day": 3, "mark": "P", "alt": None},
            ],
            "written_total": 1.0,
        },
    ],
}


def _make_fake_jpeg() -> bytes:
    """Create a minimal valid 1x1 JPEG so image_prep.prepare() can run."""
    from PIL import Image
    buf = io.BytesIO()
    img = Image.new("RGB", (10, 10), color=(128, 128, 128))
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def fake_image(tmp_path: Path) -> str:
    """Write a fake JPEG to a temp file and return its path."""
    img_path = tmp_path / "test_register.jpg"
    img_path.write_bytes(_make_fake_jpeg())
    return str(img_path)


# ---------------------------------------------------------------------------
# Helper: build the patched RawReading object the mock LLM will return
# ---------------------------------------------------------------------------

def _make_raw_reading_mock():
    """Build a RawReading pydantic instance from the canned dict."""
    from ai_core.register_reader import RawReading
    return RawReading.model_validate(_CANNED_READING)


# ---------------------------------------------------------------------------
# Test: mock mode — schema-valid RegisterExtraction returned
# ---------------------------------------------------------------------------

class TestReadRegisterMocked:
    """Tests that patch LLM.json_call to return canned readings."""

    @pytest.mark.asyncio
    async def test_returns_register_extraction(self, fake_image: str):
        """read_register should return a valid RegisterExtraction."""
        mock_reading = _make_raw_reading_mock()

        with patch("ai_core.llm.LLM") as MockLLM:
            instance = MockLLM.return_value
            instance.json_call = AsyncMock(return_value=mock_reading)

            from ai_core.register_reader import read_register
            result = await read_register(fake_image, n_samples=2)

        assert isinstance(result, RegisterExtraction)
        # Pydantic validates the model on creation; if we got here it's valid.
        # Additional field checks:
        assert result.extraction_id != ""
        assert len(result.extraction_id) == 12
        assert result.image_id != ""
        assert result.n_samples == 2
        assert len(result.rows) > 0
        assert result.elapsed_s >= 0.0

    @pytest.mark.asyncio
    async def test_header_populated(self, fake_image: str):
        mock_reading = _make_raw_reading_mock()
        with patch("ai_core.llm.LLM") as MockLLM:
            MockLLM.return_value.json_call = AsyncMock(return_value=mock_reading)
            from ai_core.register_reader import read_register
            result = await read_register(fake_image, n_samples=2)

        # Both readings agree so confidence == 1.0
        assert result.header.site_name.value == "Sunrise Towers"
        assert result.header.site_name.confidence == 1.0
        assert result.header.month.value == "9"
        assert result.header.year.value == "2026"

    @pytest.mark.asyncio
    async def test_rows_and_cells(self, fake_image: str):
        mock_reading = _make_raw_reading_mock()
        with patch("ai_core.llm.LLM") as MockLLM:
            MockLLM.return_value.json_call = AsyncMock(return_value=mock_reading)
            from ai_core.register_reader import read_register
            result = await read_register(fake_image, n_samples=2)

        assert len(result.rows) == 2
        row0 = result.rows[0]
        assert row0.name_raw == "राकेश"
        assert row0.name_latin == "Rakesh"
        # Day 1 should be "P" with confidence 1.0
        cell_d1 = next(c for c in row0.cells if c.day == 1)
        assert cell_d1.mark == Mark.present
        assert cell_d1.confidence == 1.0

    @pytest.mark.asyncio
    async def test_target_name_matching(self, fake_image: str):
        mock_reading = _make_raw_reading_mock()
        with patch("ai_core.llm.LLM") as MockLLM:
            MockLLM.return_value.json_call = AsyncMock(return_value=mock_reading)
            from ai_core.register_reader import read_register
            result = await read_register(
                fake_image, n_samples=2, target_name="Rakesh"
            )

        target_rows = [r for r in result.rows if r.is_target]
        assert len(target_rows) == 1
        assert target_rows[0].name_raw == "राकेश"
        assert target_rows[0].name_match_score >= 0.9

    @pytest.mark.asyncio
    async def test_progress_callback_called(self, fake_image: str):
        mock_reading = _make_raw_reading_mock()
        calls: list[tuple[str, float]] = []

        def _prog(stage: str, frac: float) -> None:
            calls.append((stage, frac))

        with patch("ai_core.llm.LLM") as MockLLM:
            MockLLM.return_value.json_call = AsyncMock(return_value=mock_reading)
            from ai_core.register_reader import read_register
            await read_register(fake_image, n_samples=2, progress=_prog)

        stages = [c[0] for c in calls]
        assert "preprocess" in stages
        assert any("reading" in s for s in stages)

    @pytest.mark.asyncio
    async def test_image_dimensions_set(self, fake_image: str):
        mock_reading = _make_raw_reading_mock()
        with patch("ai_core.llm.LLM") as MockLLM:
            MockLLM.return_value.json_call = AsyncMock(return_value=mock_reading)
            from ai_core.register_reader import read_register
            result = await read_register(fake_image, n_samples=2)

        assert result.image_width is not None and result.image_width > 0
        assert result.image_height is not None and result.image_height > 0

    @pytest.mark.asyncio
    async def test_models_list_populated(self, fake_image: str):
        mock_reading = _make_raw_reading_mock()
        with patch("ai_core.llm.LLM") as MockLLM:
            MockLLM.return_value.json_call = AsyncMock(return_value=mock_reading)
            from ai_core.register_reader import read_register
            result = await read_register(fake_image, n_samples=2)

        assert len(result.models) >= 1

    @pytest.mark.asyncio
    async def test_computed_total_correct(self, fake_image: str):
        """P=1, H=0.5 — Rakesh has P,P,A,H,P → 3.5."""
        mock_reading = _make_raw_reading_mock()
        with patch("ai_core.llm.LLM") as MockLLM:
            MockLLM.return_value.json_call = AsyncMock(return_value=mock_reading)
            from ai_core.register_reader import read_register
            result = await read_register(fake_image, n_samples=2)

        row0 = result.rows[0]
        assert row0.computed_total == pytest.approx(3.5)
        # Written total is also 3.5 → consistent
        assert row0.total_consistent is True

    @pytest.mark.asyncio
    async def test_one_reading_fails_still_works(self, fake_image: str):
        """If one reading throws, the other should still produce a result."""
        mock_reading = _make_raw_reading_mock()
        call_count = 0

        async def _side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("simulated LLM failure")
            return mock_reading

        with patch("ai_core.llm.LLM") as MockLLM:
            MockLLM.return_value.json_call = _side_effect
            from ai_core.register_reader import read_register
            # n_samples=2 but only 1 succeeds — should raise because < 2 valid
            with pytest.raises(ValueError, match="at least 2"):
                await read_register(fake_image, n_samples=2)

    @pytest.mark.asyncio
    async def test_n_samples_default_uses_settings(self, fake_image: str):
        """When n_samples is None, settings.readers should be used."""
        mock_reading = _make_raw_reading_mock()
        call_counts: list[int] = []

        async def _side_effect(**kwargs):
            call_counts.append(1)
            return mock_reading

        with patch("ai_core.llm.LLM") as MockLLM:
            MockLLM.return_value.json_call = _side_effect
            from ai_core.register_reader import read_register
            from ai_core.config import settings
            result = await read_register(fake_image, n_samples=None)

        assert result.n_samples == settings.readers
        assert len(call_counts) == settings.readers


# ---------------------------------------------------------------------------
# Live test (skipped unless pytest -m live and AI_MODE=real)
# ---------------------------------------------------------------------------

@pytest.mark.live
def test_live_register_reading():
    """
    Full end-to-end test: runs the real LLM on a sample register photo.

    Requires:
        - ANTHROPIC_API_KEY set in .env
        - AI_MODE=real
        - data/registers/R01.jpg present

    Run:
        PYTHONPATH=. AI_MODE=real pytest -q -m live ai_core/tests/test_register_reader.py
    """
    import os
    from pathlib import Path

    photo = Path("data/registers/R01.jpg")
    if not photo.exists():
        pytest.skip("data/registers/R01.jpg not found")

    from ai_core.register_reader import read_register

    result = asyncio.run(
        read_register(str(photo), target_name="Rakesh", n_samples=2)
    )

    assert isinstance(result, RegisterExtraction)
    assert len(result.rows) > 0
    # At least one row should have cells
    assert any(len(r.cells) > 0 for r in result.rows)
    print("\n=== Live result ===")
    print(f"  site: {result.header.site_name.value}")
    print(f"  rows: {len(result.rows)}")
    print(f"  warnings: {result.warnings}")
    print(f"  elapsed: {result.elapsed_s}s")
