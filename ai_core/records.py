"""ai_core/records.py — STUB (agent RC owns this file).

Do not implement logic here.
"""
from __future__ import annotations
from contracts.schemas import ConfirmRegisterIn, Origin, RegisterExtraction, WorkRecord


def build_work_record(
    extraction: RegisterExtraction,
    confirm: ConfirmRegisterIn,
    *,
    worker_id: str,
    origin: Origin = Origin.live,
) -> WorkRecord:
    raise NotImplementedError("records not merged yet (agent RC)")
