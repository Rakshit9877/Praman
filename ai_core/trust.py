"""ai_core/trust.py — STUB (agent RC owns this file).

Do not implement logic here.
"""
from __future__ import annotations
from contracts.schemas import ReconciliationReport, TrustResult, VoiceClaim, WageBand, WorkRecord


def score_passport(
    claim: VoiceClaim | None,
    records: list[WorkRecord],
    report: ReconciliationReport,
) -> tuple[TrustResult, dict[str, WageBand]]:
    raise NotImplementedError("trust not merged yet (agent RC)")
