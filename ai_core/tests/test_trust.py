import pytest
from contracts.schemas import ReconciliationReport, VoiceClaim, WorkRecord, Trade, SkillClass, EvidenceLevel, Origin, Flag
from ai_core.trust import compute_trust

def test_trust_score_hand_calculated():
    # Let's hand-calculate a scenario
    # coverage_full_days = 720. verified_days = 360 -> coverage = 40 * (360/720) = 20
    # attested_days = 360 -> attestation = 30 * (360/360) = 30
    # consistency = 20 - (no flags) = 20
    # claim_alignment = 10 * min(evidenced_span_years=360/260=1.38 / claim.years=2, 1) = 10 * (1.38/2) = 6.9
    # Total = 20 + 30 + 20 + 6.9 = 76.9 -> round -> 77 -> high
    
    claim = VoiceClaim(
        claim_id="c1",
        transcript="...",
        trade=Trade.mason,
        years_experience=2.0
    )
    
    # Needs some dummy records to provide evidence for attested_days
    class DummyRecord:
        def __init__(self):
            self.days_worked = 360
            self.evidence = EvidenceLevel.attested
            self.role = Trade.mason
    
    records = [DummyRecord()]
    
    report = ReconciliationReport(
        verified_days=360,
        verified_sites=1,
        attested_sites=1,
        evidenced_span_years=360/260,
        claimed_years=2.0,
        flags=[]
    )
    
    result = compute_trust(claim, records, report) # type: ignore
    assert result.score == 77
    assert result.level == "high"
    
    # 360 days is >= semi_skilled (120) but < skilled (500)
    assert result.suggested_class == SkillClass.semi_skilled

def test_trust_score_penalties():
    report = ReconciliationReport(
        verified_days=720,
        verified_sites=1,
        attested_sites=0,
        evidenced_span_years=720/260,
        flags=[
            Flag(code="SAME_DAY_TWO_SITES", severity="conflict", message="...", record_ids=[]),
            Flag(code="CLAIM_EXCEEDS_EVIDENCE", severity="warn", message="...", record_ids=[])
        ]
    )
    
    result = compute_trust(None, [], report)
    # coverage = 40 * min(720/720) = 40
    # attestation = 0
    # consistency = max(0, 20 - 10*1 - 2*1) = 8
    # claim_alignment = 5 (no claim)
    # Total = 40 + 0 + 8 + 5 = 53
    assert result.score == 53
    assert result.level == "medium"
    assert result.suggested_class == SkillClass.unskilled # Trade is None
