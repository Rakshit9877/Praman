import pytest
from datetime import date
from contracts.schemas import WorkRecord, EvidenceLevel, Origin, VoiceClaim, Flag, ReconciliationReport, Trade
from ai_core.reconcile import reconcile

def test_same_day_two_sites():
    records = [
        WorkRecord(
            record_id="r1",
            worker_id="w1",
            site_name="Site A",
            period_from=date(2026, 4, 1),
            period_to=date(2026, 4, 2),
            days_worked=2.0,
            day_marks={"2026-04-01": "P", "2026-04-02": "P"},
            evidence=EvidenceLevel.register,
            origin=Origin.live
        ),
        WorkRecord(
            record_id="r2",
            worker_id="w1",
            site_name="Site B",
            period_from=date(2026, 4, 2),
            period_to=date(2026, 4, 2),
            days_worked=0.5,
            day_marks={"2026-04-02": "H"}, # Conflict on day 2
            evidence=EvidenceLevel.register,
            origin=Origin.seeded
        )
    ]
    report = reconcile(claim=None, records=records)
    
    # Total days = 2.0 + 0.5 = 2.5
    # Conflict on 04-02: marks are 1.0 (P) and 0.5 (H). Max is 1.0. Total is 1.5. Exclusion is 1.5 - 1.0 = 0.5.
    # Verified days = 2.5 - 0.5 = 2.0
    assert report.verified_days == 2.0
    assert report.verified_sites == 2
    
    conflict_flags = [f for f in report.flags if f.code == "SAME_DAY_TWO_SITES"]
    assert len(conflict_flags) == 1
    assert conflict_flags[0].severity == "conflict"
    assert "r1" in conflict_flags[0].record_ids
    assert "r2" in conflict_flags[0].record_ids


def test_claim_gap_and_trade_mismatch():
    claim = VoiceClaim(
        claim_id="c1",
        transcript="I am a plumber with 10 years experience",
        trade=Trade.plumber,
        years_experience=10.0
    )
    records = [
        WorkRecord(
            record_id="r1",
            worker_id="w1",
            site_name="Site A",
            role=Trade.mason, # Mismatch
            period_from=date(2026, 4, 1),
            period_to=date(2026, 4, 2),
            days_worked=2.0, # Very little evidence compared to 10 years
            day_marks={"2026-04-01": "P", "2026-04-02": "P"},
            evidence=EvidenceLevel.register,
            origin=Origin.live
        )
    ]
    report = reconcile(claim=claim, records=records)
    
    assert any(f.code == "TRADE_MISMATCH" for f in report.flags)
    assert any(f.code == "CLAIM_EXCEEDS_EVIDENCE" for f in report.flags)
