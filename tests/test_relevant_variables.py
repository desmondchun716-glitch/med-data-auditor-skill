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
