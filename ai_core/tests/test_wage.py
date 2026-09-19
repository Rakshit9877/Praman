import pytest
from contracts.schemas import SkillClass
from ai_core.wage import wage_band, all_bands

def test_wage_band_fallback():
    # Use a dummy table to test fallback logic
    dummy_table = {
        "effective_from": "2026-04-01",
        "effective_to": "2026-09-30",
        "source": "Dummy Source",
        "areas": {
            "A": {"unskilled": 800, "semi_skilled": None, "skilled": 1000, "highly_skilled": None}
        }
    }
    
    # Target skill is semi_skilled, which is None in the table. Should fall back to unskilled (800).
    band = wage_band(SkillClass.semi_skilled, "A", table=dummy_table)
    
    assert band.daily_wage == 800
    assert band.unskilled_daily_wage == 800
    assert band.delta_per_day == 0.0
    assert "no official rate published for this skill class; showing unskilled rate as placeholder" in band.source
    
def test_wage_band_skilled():
    dummy_table = {
        "effective_from": "2026-04-01",
        "effective_to": "2026-09-30",
        "source": "Dummy Source",
        "areas": {
            "A": {"unskilled": 800, "semi_skilled": None, "skilled": 1000, "highly_skilled": None}
        }
    }
    
    band = wage_band(SkillClass.skilled, "A", table=dummy_table)
    
    assert band.daily_wage == 1000
    assert band.delta_per_day == 200
    assert band.delta_pct == 25.0
