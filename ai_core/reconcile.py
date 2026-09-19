"""ai_core/reconcile.py — STUB (agent RC owns this file).

Do not implement logic here.
"""
from __future__ import annotations
from contracts.schemas import Flag, ReconciliationReport, VoiceClaim, WorkRecord


def reconcile(
    claim: VoiceClaim | None,
    records: list[WorkRecord],
    extra_flags: list[Flag] | None = None,
) -> ReconciliationReport:
    raise NotImplementedError("reconcile not merged yet (agent RC)")
