"""ai_core/reconcile.py — Deterministic reconciliation rules (Agent RC)."""
from __future__ import annotations
from collections import defaultdict

from contracts.schemas import Flag, ReconciliationReport, VoiceClaim, WorkRecord
from ai_core.config import get_rules


def reconcile(
    claim: VoiceClaim | None,
    records: list[WorkRecord],
    extra_flags: list[Flag] | None = None,
) -> ReconciliationReport:
    rules = get_rules()
    flags: list[Flag] = []
    
    if extra_flags:
        flags.extend(extra_flags)

    # date -> list of (site_name, record_id, mark_value)
    date_to_sites = defaultdict(list)
    distinct_sites = set()
    total_days_worked = 0.0

    for r in records:
        distinct_sites.add(r.site_name)
        total_days_worked += r.days_worked
        for date_str, mark in r.day_marks.items():
            mark_value = 1.0 if mark == "P" else (0.5 if mark == "H" else 0.0)
            date_to_sites[date_str].append((r.site_name, r.record_id, mark_value))

    exclusion = 0.0
    for date_str, site_list in date_to_sites.items():
        unique_sites = {site for site, _, _ in site_list}
        if len(unique_sites) >= 2:
            # SAME_DAY_TWO_SITES conflict
            record_ids = list({rid for _, rid, _ in site_list})
            flags.append(
                Flag(
                    code="SAME_DAY_TWO_SITES",
                    severity="conflict",
                    message=f"Conflict: {len(unique_sites)} sites recorded on {date_str}.",
                    record_ids=sorted(record_ids)
                )
            )
            
            # exclusion for any day counted twice:
            # sum of all mark values for this day MINUS the maximum mark value for this day
            total_mark_for_day = sum(val for _, _, val in site_list)
            max_mark_for_day = max(val for _, _, val in site_list)
            exclusion += (total_mark_for_day - max_mark_for_day)

    verified_days = max(0.0, total_days_worked - exclusion)
    verified_sites = len(distinct_sites)
    
    evidenced_span_years = verified_days / rules["work_days_per_year"]

    claimed_years = None
    if claim:
        claimed_years = claim.years_experience
        if claim.years_experience and evidenced_span_years < claim.years_experience * 0.5:
            flags.append(
                Flag(
                    code="CLAIM_EXCEEDS_EVIDENCE",
                    severity="warn",
                    message=f"Claimed {claim.years_experience} years, but evidence only supports {evidenced_span_years:.1f} years.",
                    record_ids=[]
                )
            )
        
        if claim.trade:
            # If any record has a role different from the claimed trade.
            # Only consider records where role is set and different.
            # The prompt says: "any(r.role != claim.trade for r in records)"
            mismatch_records = [r.record_id for r in records if r.role and r.role != claim.trade]
            if any(r.role != claim.trade for r in records):
                flags.append(
                    Flag(
                        code="TRADE_MISMATCH",
                        severity="warn",
                        message=f"Record trade differs from claimed trade '{claim.trade}'.",
                        record_ids=sorted(mismatch_records)
                    )
                )

    # Sort flags deterministically: severity order conflict > warn > info, then by code alphabetically.
    severity_order = {"conflict": 0, "warn": 1, "info": 2}
    flags.sort(key=lambda f: (severity_order.get(f.severity, 3), f.code, f.message))

    # Calculate attested_sites (count of sites with at least one record that is EvidenceLevel.attested)
    # Note: wait, where does attested_sites come from? The struct has `attested_sites`.
    # Let's compute it.
    attested_sites = len({r.site_name for r in records if r.evidence == "attested"})

    return ReconciliationReport(
        verified_days=verified_days,
        verified_sites=verified_sites,
        attested_sites=attested_sites,
        evidenced_span_years=evidenced_span_years,
        claimed_years=claimed_years,
        flags=flags
    )
