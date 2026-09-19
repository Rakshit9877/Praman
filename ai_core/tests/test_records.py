import pytest
from datetime import date
from contracts.schemas import (
    RegisterExtraction, RegisterRow, DayCell, Mark, ConfirmRegisterIn, CellCorrection, RegisterHeader, ReadField
)
from ai_core.records import build_work_record

def _make_extraction():
    return RegisterExtraction(
        extraction_id="ext-1",
        image_id="img-1",
        header=RegisterHeader(
            site_name=ReadField(value="Site A"),
            contractor_name=ReadField(value="Contractor A"),
            month=ReadField(value="4"),
            year=ReadField(value="2026")
        ),
        rows=[
            RegisterRow(
                row_index=1,
                name_raw="Rakesh",
                computed_total=0.0,
                cells=[
                    DayCell(day=1, mark=Mark.present, confidence=1.0, needs_confirmation=False),
                    DayCell(day=2, mark=Mark.unreadable, confidence=0.0, needs_confirmation=True),
                    DayCell(day=31, mark=Mark.present, confidence=1.0, needs_confirmation=False), # Valid day in some months, not April
                ]
            )
        ],
        n_samples=3,
        models=["claude"]
    )

def test_build_work_record_missing_correction():
    ext = _make_extraction()
    confirm = ConfirmRegisterIn(
        worker_id="w-1",
        target_row_index=1,
        corrections=[] # Missing correction for day 2
    )
    with pytest.raises(ValueError, match="needs confirmation but no correction was provided"):
        build_work_record(ext, confirm, worker_id="w-1")

def test_build_work_record_invalid_date():
    ext = _make_extraction()
    # In April (month 4), day 31 is invalid.
    confirm = ConfirmRegisterIn(
        worker_id="w-1",
        target_row_index=1,
        corrections=[CellCorrection(row_index=1, day=2, mark=Mark.present)]
    )
    with pytest.raises(ValueError, match="Invalid date"):
        build_work_record(ext, confirm, worker_id="w-1")

def test_build_work_record_success():
    ext = _make_extraction()
    ext.rows[0].cells = [
        DayCell(day=1, mark=Mark.present, confidence=1.0, needs_confirmation=False),
        DayCell(day=2, mark=Mark.unreadable, confidence=0.0, needs_confirmation=True),
    ]
    confirm = ConfirmRegisterIn(
        worker_id="w-1",
        target_row_index=1,
        corrections=[CellCorrection(row_index=1, day=2, mark=Mark.half)]
    )
    record = build_work_record(ext, confirm, worker_id="w-1")
    
    assert record.days_worked == 1.5
    assert record.period_from == date(2026, 4, 1)
    assert record.period_to == date(2026, 4, 2)
    assert record.cells_confirmed_by_worker == 1
    assert record.cells_auto_accepted == 1
    assert "2026-04-01" in record.day_marks
    assert record.day_marks["2026-04-01"] == "P"
    assert record.day_marks["2026-04-02"] == "H"
