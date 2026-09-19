"""ai_core/tests/test_aggregate.py — Unit tests for aggregate.py.

All tests are offline (no network, no LLM).  They build RawReading-like
dicts as fixtures and verify the aggregate_readings() output.

Run with:
    PYTHONPATH=. pytest -q -m "not live" ai_core/tests/test_aggregate.py
"""
from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# We test via the public function
# ---------------------------------------------------------------------------
from ai_core.aggregate import aggregate_readings, _wratio, _plurality


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_reading(
    rows: list[dict],
    *,
    site_name: str | None = "Test Site",
    contractor_name: str | None = "Suresh",
    month: str | None = "9",
    year: str | None = "2026",
) -> dict:
    """Build a minimal RawReading dict."""
    return {
        "header": {
            "site_name": site_name,
            "contractor_name": contractor_name,
            "month": month,
            "year": year,
        },
        "rows": rows,
    }


def _make_row(
    name_raw: str,
    name_latin: str | None = None,
    cells: list[dict] | None = None,
    written_total: float | None = None,
    bbox: list[float] | None = None,
) -> dict:
    return {
        "name_raw": name_raw,
        "name_latin": name_latin,
        "bbox": bbox,
        "cells": cells or [],
        "written_total": written_total,
    }


def _cell(day: int, mark: str, alt: str | None = None) -> dict:
    return {"day": day, "mark": mark, "alt": alt}


# ===========================================================================
# 1. Unanimous cells — all readings agree → confidence = 1.0, no confirmation
# ===========================================================================

class TestUnanimousCells:
    def test_all_agree_no_confirmation(self):
        readings = [
            _make_reading([
                _make_row("Ravi", "Ravi", [_cell(1, "P"), _cell(2, "A"), _cell(3, "H")])
            ]),
            _make_reading([
                _make_row("Ravi", "Ravi", [_cell(1, "P"), _cell(2, "A"), _cell(3, "H")])
            ]),
        ]
        header, rows, warnings = aggregate_readings(readings)
        assert len(rows) == 1
        cells_by_day = {c.day: c for c in rows[0].cells}

        assert cells_by_day[1].mark.value == "P"
        assert cells_by_day[1].confidence == 1.0
        assert not cells_by_day[1].needs_confirmation

        assert cells_by_day[2].mark.value == "A"
        assert not cells_by_day[2].needs_confirmation

        assert cells_by_day[3].mark.value == "H"
        assert not cells_by_day[3].needs_confirmation

    def test_header_unanimous(self):
        readings = [
            _make_reading([], site_name="Alpha Tower", month="3"),
            _make_reading([], site_name="Alpha Tower", month="3"),
        ]
        header, rows, warnings = aggregate_readings(readings)
        assert header.site_name.value == "Alpha Tower"
        assert header.site_name.confidence == 1.0
        assert not header.site_name.needs_confirmation
        assert header.month.value == "3"


# ===========================================================================
# 2. Two readings, one disagrees (2-1 split with 3 samples)
# ===========================================================================

class TestSplit21:
    def test_2_readings_split(self):
        """With 2 readings and a split P vs A, we get a tie → '?' with conf=0.5."""
        readings = [
            _make_reading([_make_row("Mohan", "Mohan", [_cell(5, "P")])]),
            _make_reading([_make_row("Mohan", "Mohan", [_cell(5, "A")])]),
        ]
        header, rows, warnings = aggregate_readings(readings)
        assert len(rows) == 1
        cell = next(c for c in rows[0].cells if c.day == 5)
        # P and A tie → winner is "?", confidence = 1/2 = 0.5
        assert cell.mark.value == "?"
        assert cell.confidence == pytest.approx(0.5)
        assert cell.needs_confirmation
        assert "readers_disagree" in cell.reasons

    def test_3_readings_2_1_split_winner_chosen(self):
        readings = [
            _make_reading([_make_row("Amit", "Amit", [_cell(10, "P")])]),
            _make_reading([_make_row("Amit", "Amit", [_cell(10, "P")])]),
            _make_reading([_make_row("Amit", "Amit", [_cell(10, "A")])]),
        ]
        header, rows, warnings = aggregate_readings(readings)
        cell = next(c for c in rows[0].cells if c.day == 10)
        assert cell.mark.value == "P"
        # 2/3 = 0.6666... rounds to 0.6667 at 4dp
        assert abs(cell.confidence - 2/3) < 0.001
        assert cell.needs_confirmation           # conf < 1.0 (confirm_below_agreement=1.0)
        assert "readers_disagree" in cell.reasons


# ===========================================================================
# 3. Three-way tie (3 samples, 3 different marks) → "?"
# ===========================================================================

class TestThreeWayTie:
    def test_3way_tie_produces_unreadable(self):
        readings = [
            _make_reading([_make_row("Suresh", "Suresh", [_cell(15, "P")])]),
            _make_reading([_make_row("Suresh", "Suresh", [_cell(15, "A")])]),
            _make_reading([_make_row("Suresh", "Suresh", [_cell(15, "H")])]),
        ]
        header, rows, warnings = aggregate_readings(readings)
        cell = next(c for c in rows[0].cells if c.day == 15)
        assert cell.mark.value == "?"
        assert "unreadable" in cell.reasons
        assert cell.needs_confirmation


# ===========================================================================
# 4. Total mismatch
# ===========================================================================

class TestTotalMismatch:
    def test_mismatch_flags_uncertain_cells(self):
        """When written_total != computed_total, flagged cells get 'total_mismatch'."""
        readings = [
            _make_reading([
                _make_row(
                    "Lalit", "Lalit",
                    [_cell(1, "P"), _cell(2, "P"), _cell(3, "A")],
                    written_total=3,   # should be 2.0, so mismatch
                )
            ]),
            _make_reading([
                _make_row(
                    "Lalit", "Lalit",
                    [_cell(1, "P"), _cell(2, "A"), _cell(3, "A")],  # disagrees on day 2
                    written_total=3,
                )
            ]),
        ]
        header, rows, warnings = aggregate_readings(readings)
        row = rows[0]
        # Day 2 is uncertain (disagreement → needs_confirmation)
        cell_d2 = next(c for c in row.cells if c.day == 2)
        assert cell_d2.needs_confirmation
        # With mismatch, total_mismatch should be added
        assert "total_mismatch" in cell_d2.reasons
        assert row.total_consistent is False

    def test_mismatch_all_agree_row_warning(self):
        """If all cells agree (no uncertain cells), a row-level warning is added."""
        readings = [
            _make_reading([
                _make_row(
                    "Kiran", "Kiran",
                    [_cell(1, "P"), _cell(2, "P")],
                    written_total=5,   # 2.0 computed, clearly wrong
                )
            ]),
            _make_reading([
                _make_row(
                    "Kiran", "Kiran",
                    [_cell(1, "P"), _cell(2, "P")],
                    written_total=5,
                )
            ]),
        ]
        header, rows, warnings = aggregate_readings(readings)
        row = rows[0]
        assert row.total_consistent is False
        # A row-level warning must appear in the returned warnings list
        assert any("total mismatch" in w.lower() or "mismatch" in w.lower()
                   for w in warnings)

    def test_matching_total_is_consistent(self):
        readings = [
            _make_reading([_make_row("Rahul", "Rahul", [_cell(1, "P"), _cell(2, "H")], written_total=1.5)]),
            _make_reading([_make_row("Rahul", "Rahul", [_cell(1, "P"), _cell(2, "H")], written_total=1.5)]),
        ]
        _, rows, _ = aggregate_readings(readings)
        assert rows[0].total_consistent is True
        assert rows[0].computed_total == pytest.approx(1.5)


# ===========================================================================
# 5. Name matching — Devanagari vs Latin
# ===========================================================================

class TestNameMatching:
    def test_exact_latin_match(self):
        readings = [
            _make_reading([
                _make_row("Rakesh", "Rakesh", [_cell(1, "P")]),
                _make_row("Vijay",  "Vijay",  [_cell(1, "A")]),
            ]),
            _make_reading([
                _make_row("Rakesh", "Rakesh", [_cell(1, "P")]),
                _make_row("Vijay",  "Vijay",  [_cell(1, "A")]),
            ]),
        ]
        _, rows, _ = aggregate_readings(readings, target_name="Rakesh")
        target_rows = [r for r in rows if r.is_target]
        assert len(target_rows) == 1
        assert target_rows[0].name_raw == "Rakesh"
        assert target_rows[0].name_match_score >= 0.9

    def test_devanagari_name_match(self):
        """'राकेश' should fuzzy-match 'Rakesh' via name_latin='Rakesh'."""
        readings = [
            _make_reading([
                _make_row("राकेश", "Rakesh", [_cell(1, "P")]),
                _make_row("सुरेश", "Suresh", [_cell(1, "A")]),
            ]),
            _make_reading([
                _make_row("राकेश", "Rakesh", [_cell(1, "P")]),
                _make_row("सुरेश", "Suresh", [_cell(1, "A")]),
            ]),
        ]
        _, rows, _ = aggregate_readings(readings, target_name="Rakesh")
        target_rows = [r for r in rows if r.is_target]
        assert len(target_rows) == 1
        assert target_rows[0].name_raw == "राकेश"

    def test_no_target_below_threshold(self):
        """If best score is below name_match_min, no row is target."""
        readings = [
            _make_reading([_make_row("XXXX", "XXXX", [_cell(1, "P")])]),
            _make_reading([_make_row("XXXX", "XXXX", [_cell(1, "P")])]),
        ]
        _, rows, _ = aggregate_readings(readings, target_name="Completely Different")
        # Score should be very low — no row marked as target
        assert all(not r.is_target for r in rows)

    def test_devanagari_raw_match_without_latin(self):
        """Match 'राकेश' via name_raw when name_latin is None."""
        readings = [
            _make_reading([
                _make_row("राकेश", None, [_cell(1, "P")]),
            ]),
            _make_reading([
                _make_row("राकेश", None, [_cell(1, "P")]),
            ]),
        ]
        # WRatio between "राकेश" and "राकेश" should be 1.0
        _, rows, _ = aggregate_readings(readings, target_name="राकेश")
        assert rows[0].is_target
        assert rows[0].name_match_score == pytest.approx(1.0)


# ===========================================================================
# 6. Insufficient valid readings → ValueError
# ===========================================================================

class TestInsufficientReadings:
    def test_one_valid_raises(self):
        readings = [
            _make_reading([_make_row("A", "A", [_cell(1, "P")])]),
            {"invalid": True},  # will be dropped
        ]
        with pytest.raises(ValueError, match="at least 2 valid"):
            aggregate_readings(readings)

    def test_zero_valid_raises(self):
        readings = [{"bad": 1}, {"also": "bad"}]
        with pytest.raises(ValueError):
            aggregate_readings(readings)


# ===========================================================================
# 7. Row drop when row appears in < 50% of readings
# ===========================================================================

class TestRowDrop:
    def test_row_missing_in_second_reading_kept(self):
        """Row present in 1/2 readings (50%) — at boundary, should be kept."""
        readings = [
            _make_reading([
                _make_row("Alpha", "Alpha", [_cell(1, "P")]),
            ]),
            _make_reading([
                _make_row("Alpha", "Alpha", [_cell(1, "P")]),
            ]),
        ]
        _, rows, warnings = aggregate_readings(readings)
        assert len(rows) == 1

    def test_row_in_only_one_of_three_dropped(self):
        """Row appearing in 1/3 readings (33%) should be dropped with a warning."""
        readings = [
            _make_reading([
                _make_row("Alpha", "Alpha", [_cell(1, "P")]),
                _make_row("Ghost", "Ghost", [_cell(1, "P")]),  # only in reading 0
            ]),
            _make_reading([_make_row("Alpha", "Alpha", [_cell(1, "P")])]),
            _make_reading([_make_row("Alpha", "Alpha", [_cell(1, "P")])]),
        ]
        _, rows, warnings = aggregate_readings(readings)
        row_names = [r.name_raw for r in rows]
        assert "Ghost" not in row_names
        assert any("Ghost" in w or "dropped" in w for w in warnings)


# ===========================================================================
# 8. Header with missing / disagreeing values
# ===========================================================================

class TestHeaderVoting:
    def test_split_header_needs_confirmation(self):
        readings = [
            _make_reading([], site_name="Site A", contractor_name="Ramesh"),
            _make_reading([], site_name="Site B", contractor_name="Ramesh"),
        ]
        header, _, _ = aggregate_readings(readings)
        assert header.site_name.needs_confirmation
        assert header.contractor_name.value == "Ramesh"
        assert not header.contractor_name.needs_confirmation

    def test_none_header_field(self):
        readings = [
            _make_reading([], month=None),
            _make_reading([], month=None),
        ]
        header, _, _ = aggregate_readings(readings)
        assert header.month.value is None
        assert header.month.needs_confirmation


# ===========================================================================
# 9. Internal helpers
# ===========================================================================

class TestHelpers:
    def test_wratio_none(self):
        assert _wratio(None, "hello") == 0.0
        assert _wratio("hello", None) == 0.0
        assert _wratio(None, None) == 0.0

    def test_plurality_single(self):
        winner, count, alts = _plurality(["P", "P", "P"])
        assert winner == "P"
        assert count == 3
        assert alts == []

    def test_plurality_tie_returns_question(self):
        winner, count, alts = _plurality(["P", "A"])
        assert winner == "?"

    def test_plurality_majority(self):
        winner, count, alts = _plurality(["P", "P", "A"])
        assert winner == "P"
        assert count == 2
        assert "A" in alts


# ===========================================================================
# 10. BBox median
# ===========================================================================

class TestBbox:
    def test_bbox_set_when_two_readings_have_it(self):
        readings = [
            _make_reading([
                _make_row("X", "X", [_cell(1, "P")], bbox=[0.1, 0.2, 0.9, 0.3])
            ]),
            _make_reading([
                _make_row("X", "X", [_cell(1, "P")], bbox=[0.1, 0.2, 0.9, 0.3])
            ]),
        ]
        _, rows, _ = aggregate_readings(readings)
        assert rows[0].bbox is not None
        assert len(rows[0].bbox) == 4

    def test_bbox_none_when_only_one_reading_has_it(self):
        readings = [
            _make_reading([
                _make_row("X", "X", [_cell(1, "P")], bbox=[0.1, 0.2, 0.9, 0.3])
            ]),
            _make_reading([
                _make_row("X", "X", [_cell(1, "P")], bbox=None)
            ]),
        ]
        _, rows, _ = aggregate_readings(readings)
        # Only 1 reading has bbox, so median cannot be computed (need >= 2)
        assert rows[0].bbox is None


# ===========================================================================
# 11. Multi-row alignment
# ===========================================================================

class TestRowAlignment:
    def test_rows_aligned_by_name_similarity(self):
        """Reading 2 has rows in different order; they should still be aligned."""
        readings = [
            _make_reading([
                _make_row("Ramesh", "Ramesh", [_cell(1, "P")]),
                _make_row("Suresh", "Suresh", [_cell(1, "A")]),
            ]),
            _make_reading([
                _make_row("Suresh", "Suresh", [_cell(1, "A")]),
                _make_row("Ramesh", "Ramesh", [_cell(1, "P")]),
            ]),
        ]
        _, rows, _ = aggregate_readings(readings)
        # Row 0 should be Ramesh (reference reading order)
        assert rows[0].name_raw == "Ramesh"
        cell_r = next(c for c in rows[0].cells if c.day == 1)
        assert cell_r.mark.value == "P"
        assert cell_r.confidence == 1.0

    def test_computed_total_correct(self):
        readings = [
            _make_reading([_make_row("T", "T", [_cell(1, "P"), _cell(2, "H"), _cell(3, "A")])]),
            _make_reading([_make_row("T", "T", [_cell(1, "P"), _cell(2, "H"), _cell(3, "A")])]),
        ]
        _, rows, _ = aggregate_readings(readings)
        assert rows[0].computed_total == pytest.approx(1.5)
