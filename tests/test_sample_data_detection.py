from __future__ import annotations

from conftest import load_script
from core.medical_rules import check_medical_rules
from core.privacy_checker import check_privacy_risks
from core.profiler import profile_dataset
from core.schemas import validate_warning_schema
from core.statistical_risks import check_statistical_risks
from core.variable_mapper import identify_variable_roles


sample_mod = load_script("sample_generator_test", "scripts/01_generate_sample_data.py")


def test_synthetic_sample_detects_injected_audit_issues() -> None:
    df = sample_mod.generate_sample_data(n_rows=300, seed=42)
    profile = profile_dataset(df)
    variable_roles = identify_variable_roles(
        "Is BMI associated with hypertension after adjusting for age and sex?",
        list(df.columns),
    )

    medical_warnings = check_medical_rules(df)
    statistical_warnings = check_statistical_risks(df, profile=profile, variable_roles=variable_roles)
    privacy_warnings = check_privacy_risks(df)
    warnings = medical_warnings + statistical_warnings + privacy_warnings
    issue_ids = {warning["issue_id"] for warning in warnings}

    assert "MED_RANGE_AGE" in issue_ids
    assert "MED_RANGE_BMI" in issue_ids
    assert "MED_LOGIC_001" in issue_ids
    assert "MED_LOGIC_002" in issue_ids
    assert "MED_LOGIC_003" in issue_ids
    assert "MED_DUPLICATE_PATIENT_ID" in issue_ids
    assert "STAT_KEY_MISSING_BMI" in issue_ids
    assert "STAT_OUTCOME_IMBALANCE_HYPERTENSION" in issue_ids
    assert "PRIV_DIRECT_IDENTIFIER" in issue_ids
    assert all(validate_warning_schema(warning) for warning in warnings)
