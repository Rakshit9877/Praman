"""ai_core/wage.py — Wage band logic (Agent RC)."""
from __future__ import annotations

from typing import Literal
from datetime import datetime

from contracts.schemas import SkillClass, WageBand
from ai_core.config import get_wage_table, get_rules


def wage_band(
    skill_class: SkillClass, 
    area: Literal["A", "B", "C"], 
    table: dict | None = None
) -> WageBand:
    if table is None:
        table = get_wage_table()
        
    rules = get_rules()
    
    area_data = table["areas"][area]
    unskilled_wage = area_data["unskilled"]
    
    target_wage = area_data.get(skill_class.value)
    
    source_note = table["source"]
    if target_wage is None:
        target_wage = unskilled_wage
        source_note += " (note: no official rate published for this skill class; showing unskilled rate as placeholder)"

    delta_per_day = target_wage - unskilled_wage
    delta_pct = (delta_per_day / unskilled_wage) * 100.0 if unskilled_wage else 0.0
    monthly_delta_26d = delta_per_day * rules.get("work_days_per_month", 26)

    # Convert date strings to date objects
    effective_from = datetime.strptime(table["effective_from"], "%Y-%m-%d").date()
    effective_to = datetime.strptime(table["effective_to"], "%Y-%m-%d").date()

    return WageBand(
        area=area,
        suggested_class=skill_class,
        daily_wage=target_wage,
        unskilled_daily_wage=unskilled_wage,
        delta_per_day=delta_per_day,
        delta_pct=delta_pct,
        monthly_delta_26d=monthly_delta_26d,
        source=source_note,
        effective_from=effective_from,
        effective_to=effective_to
    )


def all_bands(skill_class: SkillClass) -> dict[str, WageBand]:
    table = get_wage_table()
    return {
        "A": wage_band(skill_class, "A", table),
        "B": wage_band(skill_class, "B", table),
        "C": wage_band(skill_class, "C", table),
    }

# Keep the original stub name for compatibility if api.py was expecting get_wage_bands?
# Ah, the prompt says "all_bands(skill_class) -> dict[str, WageBand]"
# Wait, in the stub it's `get_wage_bands`!
# The api.py says `trust.score_passport` which combines trust + wage.
# But just in case, I will also implement `get_wage_bands = all_bands` to not break anything relying on the stub name, though the prompt says to call it `all_bands`.
def get_wage_bands(suggested_class: SkillClass) -> dict[str, WageBand]:
    return all_bands(suggested_class)
