from __future__ import annotations

import pandas as pd

from conftest import load_script


rules_mod = load_script("rule_checks_test", "scripts/03_rule_checks.py")


def test_medical_rules_detect_injected_plausibility_issues() -> None:
    df = pd.DataFrame(
        {
            "patient_id": ["P1", "P1", "P2", "P3"],
            "age": [150, 40, -3, 55],
            "bmi": [25, 90, 5, 27],
            "sbp": [120, 80, 130, 140],
            "dbp": [80, 120, 85, 90],
            "sex": ["Male", "M", "Female", "F"],
            "visit_date": ["2024-05-01", "2024-05-01", "2024-03-01", "2024-01-01"],
            "death_date": ["", "", "2024-02-01", ""],
            "follow_up_days": [30, -1, 50, 40],
        }
    )

    warnings = rules_mod.check_medical_rules(df)
    issue_ids = {warning["issue_id"] for warning in warnings}

    assert "MED_RANGE_AGE" in issue_ids
    assert "MED_RANGE_BMI" in issue_ids
    assert "MED_LOGIC_001" in issue_ids
    assert "MED_LOGIC_002" in issue_ids
    assert "MED_LOGIC_003" in issue_ids
    assert "MED_DUPLICATE_PATIENT_ID" in issue_ids
    assert "MED_SEX_CODING_INCONSISTENCY" in issue_ids
