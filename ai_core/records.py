"""ai_core/records.py — Work records logic (Agent RC)."""
from __future__ import annotations

import uuid
from datetime import date
from collections import defaultdict

from contracts.schemas import ConfirmRegisterIn, Origin, RegisterExtraction, WorkRecord, EvidenceLevel


def build_work_record(
    extraction: RegisterExtraction,
    confirm: ConfirmRegisterIn,
    *,
    worker_id: str,
    origin: Origin = Origin.live,
) -> WorkRecord:
    # 1. Find the target row
    target_row = None
    for row in extraction.rows:
        if row.row_index == confirm.target_row_index:
            target_row = row
            break
    
    if not target_row:
        raise ValueError(f"Row {confirm.target_row_index} not found in extraction")

    # 2. Apply corrections to cells
    # We index corrections by day for the target row
    corrections_by_day = {}
    for c in confirm.corrections:
        if c.row_index == confirm.target_row_index:
            corrections_by_day[c.day] = c.mark

    final_cells = {}
    for cell in target_row.cells:
        if cell.needs_confirmation and cell.day not in corrections_by_day:
            raise ValueError(f"Cell for day {cell.day} needs confirmation but no correction was provided.")
        final_cells[cell.day] = corrections_by_day.get(cell.day, cell.mark)

    # 3. Determine month and year
    # Fallback logic: confirm overrides > extraction header > default to current if somehow missing
    try:
        month = confirm.month or int(extraction.header.month.value)  # type: ignore
        year = confirm.year or int(extraction.header.year.value)     # type: ignore
    except (ValueError, TypeError, AttributeError):
        today = date.today()
        month = today.month
        year = today.year

    # 4. Build day_marks and calculate days_worked
    day_marks = {}
    days_worked = 0.0
    dates_worked = []
    
    for day, mark in final_cells.items():
        if mark in ("P", "H"):
            try:
                dt = date(year, month, day)
                iso_date = dt.isoformat()
                day_marks[iso_date] = mark
                dates_worked.append(dt)
                if mark == "P":
                    days_worked += 1.0
                elif mark == "H":
                    days_worked += 0.5
            except ValueError:
                raise ValueError(f"Invalid date: year={year}, month={month}, day={day}")

    if not dates_worked:
        # If no days worked, period_from and period_to fallback to beginning/end of the month?
        # Actually, let's just use the first of the month, or today if that fails.
        try:
            period_from = date(year, month, 1)
            period_to = date(year, month, 1)
        except ValueError:
            period_from = date.today()
            period_to = date.today()
    else:
        dates_worked.sort()
        period_from = dates_worked[0]
        period_to = dates_worked[-1]

    site_name = confirm.site_name or (extraction.header.site_name.value if extraction.header.site_name else "Unknown Site")
    employer_name = confirm.employer_name or (extraction.header.contractor_name.value if extraction.header.contractor_name else None)

    return WorkRecord(
        record_id=str(uuid.uuid4()),
        worker_id=worker_id,
        site_name=site_name,
        employer_name=employer_name,
        city=confirm.city,
        role=confirm.role,
        period_from=period_from,
        period_to=period_to,
        days_worked=days_worked,
        day_marks=day_marks,
        evidence=EvidenceLevel.register,
        origin=origin,
        image_id=extraction.image_id,
        cells_confirmed_by_worker=len(corrections_by_day),
        cells_auto_accepted=sum(1 for c in target_row.cells if not c.needs_confirmation),
        attestation_id=None,
        attestation_status=None
    )
