"""ai_core/trust.py — Trust score and classification (Agent RC)."""
from __future__ import annotations

from contracts.schemas import ReconciliationReport, TrustResult, VoiceClaim, WageBand, WorkRecord, SkillClass, EvidenceLevel
from ai_core.config import get_rules
from ai_core.wage import all_bands


def compute_trust(
    claim: VoiceClaim | None,
    records: list[WorkRecord],
    report: ReconciliationReport,
) -> TrustResult:
    rules = get_rules()
    
    # 1. Coverage
    coverage_max = rules["trust"]["coverage_full_days"]
    coverage = 40.0 * min(report.verified_days / coverage_max, 1.0)
    
    # 2. Attestation
    attested_days = sum(r.days_worked for r in records if r.evidence == EvidenceLevel.attested)
    attestation = 30.0 * (attested_days / report.verified_days) if report.verified_days > 0 else 0.0
    
    # 3. Consistency
    conflict_count = sum(1 for f in report.flags if f.severity == "conflict")
    warn_count = sum(1 for f in report.flags if f.severity == "warn")
    consistency = max(0.0, 20.0 - (10.0 * conflict_count) - (2.0 * warn_count))
    
    # 4. Claim Alignment
    if claim and claim.years_experience:
        claim_alignment = 10.0 * min(report.evidenced_span_years / claim.years_experience, 1.0)
    else:
        claim_alignment = 5.0
        
    # Score and level
    score = round(coverage + attestation + consistency + claim_alignment)
    level_high_thresh = rules["trust"].get("level_high", 70)
    level_medium_thresh = rules["trust"].get("level_medium", 40)
    
    if score >= level_high_thresh:
        level = "high"
    elif score >= level_medium_thresh:
        level = "medium"
    else:
        level = "low"
        
    # Suggested class
    trade = None
    if claim and claim.trade:
        trade = claim.trade.value
    elif records and any(r.role for r in records):
        # Fallback to the role from the latest record if no claim exists
        for r in reversed(records):
            if r.role:
                trade = r.role.value
                break

    skilled_trades = rules["skilled_trades"]
    thresholds = rules["skill_thresholds"]
    
    if trade in skilled_trades and report.verified_days >= thresholds["skilled_min_days"] and report.attested_sites >= thresholds["skilled_min_attested_sites"]:
        suggested_class = SkillClass.skilled
        class_reason = f"{report.verified_days:.0f} verified days across {report.verified_sites} sites, {report.attested_sites} employer-attested — meets the skilled threshold of {thresholds['skilled_min_days']} days + {thresholds['skilled_min_attested_sites']} attestation."
    elif trade in skilled_trades and report.verified_days >= thresholds["semi_skilled_min_days"]:
        suggested_class = SkillClass.semi_skilled
        class_reason = f"{report.verified_days:.0f} verified days across {report.verified_sites} sites — meets the semi-skilled threshold of {thresholds['semi_skilled_min_days']} days."
    else:
        suggested_class = SkillClass.unskilled
        if trade not in skilled_trades:
            class_reason = f"Trade '{trade}' is not in the recognized skilled trades list, defaulting to unskilled."
        else:
            class_reason = f"{report.verified_days:.0f} verified days is below the {thresholds['semi_skilled_min_days']} days threshold for semi-skilled."
        
    return TrustResult(
        score=score,
        level=level,
        breakdown={
            "coverage": coverage,
            "attestation": attestation,
            "consistency": consistency,
            "claim_alignment": claim_alignment
        },
        suggested_class=suggested_class,
        class_reason=class_reason
    )


def score_passport(
    claim: VoiceClaim | None,
    records: list[WorkRecord],
    report: ReconciliationReport,
) -> tuple[TrustResult, dict[str, WageBand]]:
    trust_result = compute_trust(claim, records, report)
    wage_bands = all_bands(trust_result.suggested_class)
    return trust_result, wage_bands
