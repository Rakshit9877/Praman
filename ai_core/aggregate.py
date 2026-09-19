"""ai_core/aggregate.py — Aggregate multiple raw register readings into a RegisterExtraction.

All functions are pure (no network, no filesystem).  Fully unit-tested in
ai_core/tests/test_aggregate.py.

Key design:
- Confidence comes from AGREEMENT across readings, not from the LLM's self-report.
- Disagreement, unreadable marks, and written-total mismatches all trigger
  needs_confirmation=True so the worker is asked to confirm those cells.
"""
from __future__ import annotations

import logging
import statistics
from collections import Counter
from typing import Any, Optional

from contracts.schemas import (
    DayCell,
    Mark,
    ReadField,
    RegisterExtraction,
    RegisterHeader,
    RegisterRow,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rules helper (lazy-loaded to avoid circular imports at module level)
# ---------------------------------------------------------------------------

def _confirm_below() -> float:
    """Return the agreement threshold below which a cell needs confirmation."""
    from ai_core.config import get_rules
    return float(get_rules().get("confirm_below_agreement", 1.0))


def _name_match_min() -> float:
    """Return the minimum fuzzy-match score to declare is_target."""
    from ai_core.config import get_rules
    return float(get_rules().get("name_match_min", 0.6))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _wratio(a: Optional[str], b: Optional[str]) -> float:
    """rapidfuzz WRatio, normalised to 0..1.  Returns 0.0 for None inputs."""
    if not a or not b:
        return 0.0
    from rapidfuzz import fuzz
    return fuzz.WRatio(a, b) / 100.0


def _plurality(votes: list[Any]) -> tuple[Any, int, list[Any]]:
    """Return (winner, winner_count, sorted_alternatives).

    If there is a tie for the top position, winner is '?' and winner_count is
    the tied count (so confidence = tied_count / n_valid, not 0).
    Returns sorted alternatives (all values other than winner, most common first).
    """
    if not votes:
        raise ValueError("Cannot take plurality of empty vote list")
    counter = Counter(votes)
    max_count = max(counter.values())
    winners = [v for v, c in counter.items() if c == max_count]
    if len(winners) == 1:
        winner = winners[0]
        winner_count = max_count
    else:
        # Tie: synthetic winner is "?"; winner_count = votes for any tied option
        winner = "?"
        winner_count = max_count  # each tied option had this many votes
    alts = [v for v, _ in counter.most_common() if v != winner]
    return winner, winner_count, alts


# ---------------------------------------------------------------------------
# Row alignment
# ---------------------------------------------------------------------------

def _align_rows(
    reference_rows: list[dict],
    other_rows: list[dict],
) -> list[Optional[dict]]:
    """Align *other_rows* to *reference_rows* by name similarity.

    Returns a list of the same length as *reference_rows*.  Each element is
    the best-matched row from *other_rows*, or None if no match exists.

    Uses rapidfuzz WRatio on (name_latin or name_raw).  Each row in
    *other_rows* is used at most once (greedy best-match).
    """
    from rapidfuzz import fuzz

    matched: list[Optional[dict]] = [None] * len(reference_rows)
    used_indices: set[int] = set()

    for ref_idx, ref_row in enumerate(reference_rows):
        ref_name_l = ref_row.get("name_latin") or ref_row.get("name_raw") or ""
        ref_name_r = ref_row.get("name_raw") or ""

        best_score = -1.0
        best_other_idx = -1
        for o_idx, o_row in enumerate(other_rows):
            if o_idx in used_indices:
                continue
            o_name_l = o_row.get("name_latin") or o_row.get("name_raw") or ""
            o_name_r = o_row.get("name_raw") or ""
            score = max(
                fuzz.WRatio(ref_name_l, o_name_l) if ref_name_l and o_name_l else 0.0,
                fuzz.WRatio(ref_name_r, o_name_r) if ref_name_r and o_name_r else 0.0,
            )
            if score > best_score:
                best_score = score
                best_other_idx = o_idx

        # Accept any match (even a weak one) — caller handles confidence
        if best_other_idx >= 0:
            matched[ref_idx] = other_rows[best_other_idx]
            used_indices.add(best_other_idx)

    return matched


# ---------------------------------------------------------------------------
# Public aggregation entry point
# ---------------------------------------------------------------------------

def aggregate_readings(
    raw_readings: list[dict],
    *,
    target_name: Optional[str] = None,
    n_valid_min: int = 2,
) -> tuple[RegisterHeader, list[RegisterRow], list[str]]:
    """Aggregate a list of raw RawReading dicts into contract schema objects.

    Parameters
    ----------
    raw_readings:
        List of dicts matching the RawReading shape (as produced by
        register_reader._to_raw_dict).  Invalid / unparseable entries are
        dropped with a warning.
    target_name:
        If provided, the name to fuzzy-match against each row's name_raw /
        name_latin.  The single best-matching row gets is_target=True.
    n_valid_min:
        Raise ValueError if fewer than this many valid readings survive.

    Returns
    -------
    (header, rows, warnings)
    """
    warnings: list[str] = []

    # -----------------------------------------------------------------
    # Step a — validate / drop invalid readings
    # -----------------------------------------------------------------
    valid: list[dict] = []
    for i, r in enumerate(raw_readings):
        if not isinstance(r, dict):
            warnings.append(f"reading {i}: not a dict — dropped")
            continue
        if "rows" not in r or not isinstance(r.get("rows"), list):
            warnings.append(f"reading {i}: missing 'rows' field — dropped")
            continue
        valid.append(r)

    if len(valid) < n_valid_min:
        raise ValueError(
            f"Need at least {n_valid_min} valid readings, got {len(valid)}."
        )

    n_valid = len(valid)

    # -----------------------------------------------------------------
    # Step b — align rows: pick reference reading (most rows)
    # -----------------------------------------------------------------
    ref_reading = max(valid, key=lambda r: len(r.get("rows", [])))
    ref_rows: list[dict] = ref_reading.get("rows", [])
    others = [r for r in valid if r is not ref_reading]

    # For each non-reference reading, align its rows to the reference
    # aligned[reading_idx][ref_row_idx] = matched row dict or None
    aligned_per_reading: list[list[Optional[dict]]] = []
    for other in others:
        aligned_per_reading.append(_align_rows(ref_rows, other.get("rows", [])))

    # Drop reference rows that appear in < 50% of all readings
    ref_row_presence: list[int] = []
    for rr_idx in range(len(ref_rows)):
        # Reference reading counts as present; check the others
        present = 1  # ref always present
        for aln in aligned_per_reading:
            if aln[rr_idx] is not None:
                present += 1
        ref_row_presence.append(present)

    kept_ref_rows: list[dict] = []
    kept_ref_presence: list[int] = []
    kept_aligned: list[list[Optional[dict]]] = []
    for rr_idx, (rrow, pres) in enumerate(zip(ref_rows, ref_row_presence)):
        if pres / n_valid >= 0.5:
            kept_ref_rows.append(rrow)
            kept_ref_presence.append(pres)
            kept_aligned.append([aln[rr_idx] for aln in aligned_per_reading])
        else:
            warnings.append(
                f"row '{rrow.get('name_raw', '?')}' (ref_idx {rr_idx}) appeared in "
                f"only {pres}/{n_valid} readings — dropped"
            )

    # -----------------------------------------------------------------
    # Step c — header: majority vote
    # -----------------------------------------------------------------
    header = _build_header(valid, n_valid)

    # -----------------------------------------------------------------
    # Steps d/e — cells and totals per row
    # -----------------------------------------------------------------
    rows: list[RegisterRow] = []
    for rr_idx, (ref_row, presence, other_rows_aligned) in enumerate(
        zip(kept_ref_rows, kept_ref_presence, kept_aligned)
    ):
        # Collect all n_valid row dicts for this reference row
        all_row_dicts: list[dict] = [ref_row] + [
            r for r in other_rows_aligned if r is not None
        ]

        row, row_warnings = _build_row(
            row_index=rr_idx,
            all_row_dicts=all_row_dicts,
            n_valid=n_valid,
        )
        warnings.extend(row_warnings)
        rows.append(row)

    # -----------------------------------------------------------------
    # Step f — name matching
    # -----------------------------------------------------------------
    if target_name is not None:
        _apply_name_match(rows, target_name)

    # -----------------------------------------------------------------
    # Step g — bbox (median per coordinate across readings that provided one)
    # -----------------------------------------------------------------
    for rr_idx, (row, ref_row, other_rows_aligned) in enumerate(
        zip(rows, kept_ref_rows, kept_aligned)
    ):
        all_row_dicts = [ref_row] + [r for r in other_rows_aligned if r is not None]
        bbox_lists = [
            r.get("bbox")
            for r in all_row_dicts
            if r.get("bbox") and len(r["bbox"]) == 4
        ]
        if len(bbox_lists) >= 2:
            medians = [
                statistics.median([bb[i] for bb in bbox_lists]) for i in range(4)
            ]
            clipped = [max(0.0, min(1.0, v)) for v in medians]
            # Pydantic model is frozen once created; we must create a new one
            rows[rr_idx] = row.model_copy(update={"bbox": clipped})

    return header, rows, warnings


# ---------------------------------------------------------------------------
# Header building
# ---------------------------------------------------------------------------

def _build_header(valid_readings: list[dict], n_valid: int) -> RegisterHeader:
    """Build a RegisterHeader by majority-voting each field."""

    def _vote_field(field: str) -> ReadField:
        values = []
        for r in valid_readings:
            h = r.get("header") or {}
            v = h.get(field)
            if v is not None:
                values.append(str(v))

        if not values:
            return ReadField(
                value=None,
                confidence=0.0,
                needs_confirmation=True,
                alternatives=[],
            )

        counter = Counter(values)
        winner, winner_count, alts = _plurality(values)
        confidence = winner_count / n_valid
        return ReadField(
            value=winner,
            confidence=round(confidence, 4),
            needs_confirmation=confidence < 1.0 or winner is None,
            alternatives=alts,
        )

    return RegisterHeader(
        site_name=_vote_field("site_name"),
        contractor_name=_vote_field("contractor_name"),
        month=_vote_field("month"),
        year=_vote_field("year"),
    )


# ---------------------------------------------------------------------------
# Row building  (cells + totals)
# ---------------------------------------------------------------------------

def _build_row(
    *,
    row_index: int,
    all_row_dicts: list[dict],
    n_valid: int,
) -> tuple[RegisterRow, list[str]]:
    """Build a RegisterRow from the aligned row dicts across all readings."""
    row_warnings: list[str] = []
    threshold = _confirm_below()

    # Use the first (reference) row dict for name_raw / name_latin
    ref = all_row_dicts[0]
    name_raw = ref.get("name_raw") or "?"
    name_latin = ref.get("name_latin")

    # -----------------------------------------------------------------
    # Collect all day numbers seen across readings for this row
    # -----------------------------------------------------------------
    all_days: set[int] = set()
    for rd in all_row_dicts:
        for cell in rd.get("cells", []):
            day = cell.get("day")
            if isinstance(day, int) and 1 <= day <= 31:
                all_days.add(day)

    # -----------------------------------------------------------------
    # Per-day vote
    # -----------------------------------------------------------------
    day_cells: list[DayCell] = []
    for day in sorted(all_days):
        votes: list[str] = []
        alt_votes: list[str] = []
        for rd in all_row_dicts:
            matched_cell = next(
                (c for c in rd.get("cells", []) if c.get("day") == day), None
            )
            if matched_cell is not None:
                mark = matched_cell.get("mark", "?")
                # Normalise to known marks
                if mark not in ("P", "A", "H", "?"):
                    mark = "?"
                votes.append(mark)
                if matched_cell.get("alt"):
                    alt_votes.append(str(matched_cell["alt"]))

        if not votes:
            continue

        winner_raw, winner_count, alts_raw = _plurality(votes)

        # Tie → "?"
        winner_mark = Mark.unreadable if winner_raw == "?" else Mark(winner_raw)

        confidence = winner_count / n_valid
        reasons: list[str] = []
        needs_confirmation = False

        if winner_mark == Mark.unreadable:
            reasons.append("unreadable")
            needs_confirmation = True

        if len(set(votes)) > 1:
            reasons.append("readers_disagree")
            needs_confirmation = True

        if confidence < threshold:
            needs_confirmation = True

        alts_marks: list[Mark] = []
        for a in alts_raw:
            try:
                alts_marks.append(Mark(a))
            except ValueError:
                alts_marks.append(Mark.unreadable)

        day_cells.append(
            DayCell(
                day=day,
                mark=winner_mark,
                confidence=round(confidence, 4),
                needs_confirmation=needs_confirmation,
                alternatives=alts_marks,
                reasons=reasons,
            )
        )

    # -----------------------------------------------------------------
    # Totals
    # -----------------------------------------------------------------
    written_totals: list[float] = []
    for rd in all_row_dicts:
        wt = rd.get("written_total")
        if wt is not None:
            try:
                written_totals.append(float(wt))
            except (ValueError, TypeError):
                pass

    # Plurality vote for written_total
    written_total: Optional[float] = None
    if written_totals:
        winner_wt, _, _ = _plurality(written_totals)
        if winner_wt != "?":
            try:
                written_total = float(winner_wt)
            except (ValueError, TypeError):
                written_total = None

    # Computed total: P=1, H=0.5
    computed_total = sum(
        1.0 if c.mark == Mark.present else 0.5 if c.mark == Mark.half else 0.0
        for c in day_cells
    )

    total_consistent: Optional[bool] = None
    if written_total is not None:
        total_consistent = abs(written_total - computed_total) < 0.5
        if not total_consistent:
            # Flag: add "total_mismatch" to every cell that needs_confirmation or is "?"
            flagged_any = False
            new_cells: list[DayCell] = []
            for cell in day_cells:
                if cell.needs_confirmation or cell.mark == Mark.unreadable:
                    reasons_updated = list(cell.reasons)
                    if "total_mismatch" not in reasons_updated:
                        reasons_updated.append("total_mismatch")
                    new_cells.append(
                        cell.model_copy(
                            update={
                                "reasons": reasons_updated,
                                "needs_confirmation": True,
                            }
                        )
                    )
                    flagged_any = True
                else:
                    new_cells.append(cell)
            day_cells = new_cells

            if not flagged_any:
                # No existing flagged cells — add a row-level warning
                row_warnings.append(
                    f"Row '{name_raw}': total mismatch "
                    f"(written={written_total}, computed={computed_total:.1f})"
                )

    return (
        RegisterRow(
            row_index=row_index,
            name_raw=name_raw,
            name_latin=name_latin,
            name_match_score=0.0,
            is_target=False,
            bbox=None,  # set in caller if enough readings have bbox
            cells=day_cells,
            written_total=written_total,
            computed_total=round(computed_total, 1),
            total_consistent=total_consistent,
        ),
        row_warnings,
    )


# ---------------------------------------------------------------------------
# Name matching
# ---------------------------------------------------------------------------

def _apply_name_match(rows: list[RegisterRow], target_name: str) -> None:
    """Set name_match_score on all rows; set is_target=True on the best match.

    Modifies rows in-place (replaces each RegisterRow with a model_copy).
    The single best-matching row gets is_target=True only if its score >=
    name_match_min.  No row gets is_target=True on a tie (the UI will ask).
    """
    if not rows:
        return

    threshold = _name_match_min()

    # Compute scores
    scores: list[float] = []
    for row in rows:
        score = max(
            _wratio(target_name, row.name_latin),
            _wratio(target_name, row.name_raw),
        )
        scores.append(score)

    best_score = max(scores)
    best_count = scores.count(best_score)

    for i, (row, score) in enumerate(zip(rows, scores)):
        is_target = (
            score == best_score
            and best_count == 1  # no tie
            and score >= threshold
        )
        rows[i] = row.model_copy(
            update={
                "name_match_score": round(score, 4),
                "is_target": is_target,
            }
        )
