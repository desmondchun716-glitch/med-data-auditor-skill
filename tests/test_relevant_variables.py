from __future__ import annotations

from conftest import load_script


variables_mod = load_script("relevant_variables_test", "scripts/05_relevant_variables.py")


def test_identify_relevant_variables_from_question() -> None:
    result = variables_mod.identify_relevant_variables(
        "Is BMI associated with hypertension after adjusting for age and sex?",
        ["bmi", "hypertension", "age", "sex", "smoking", "diabetes"],
    )

    assert result["exposure"] == ["bmi"]
    assert result["outcome"] == ["hypertension"]
    assert result["confounders"] == ["age", "sex"]
    assert "smoking" in result["suggested_confounders"]
    assert "diabetes" in result["suggested_confounders"]


def test_infer_basic_study_design_warns_when_unspecified() -> None:
    study_design = variables_mod.infer_basic_study_design(
        __import__("pandas").DataFrame({"bmi": [25, 30], "hypertension": ["No", "Yes"]}),
        ["bmi", "hypertension"],
    )
    warnings = variables_mod.generate_study_design_warnings(
        "Does BMI cause hypertension?",
        {"exposure": ["bmi"], "outcome": ["hypertension"], "confounders": []},
        study_design,
    )

    issue_ids = {warning["issue_id"] for warning in warnings}
    assert "DESIGN_UNSPECIFIED" in issue_ids
    assert "DESIGN_CAUSAL_LANGUAGE_RISK" in issue_ids
