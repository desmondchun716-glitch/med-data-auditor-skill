from __future__ import annotations

import pandas as pd

from core.orchestrator import run_audit
from core.report_generator import generate_markdown_report, render_extraction_requests


QUESTION = "Is BMI associated with hypertension after adjusting for age and sex?"


def _write_contract_csv(path) -> None:
    pd.DataFrame(
        {
            "patient_id": ["P1", "P1", "P2", "P3"],
            "patient_name": ["Synthetic A", "Synthetic A", "Synthetic B", "Synthetic C"],
            "phone": ["111-111-1111", "111-111-1111", "222-222-2222", "333-333-3333"],
            "age": [150, 40, 50, 60],
            "sex": ["Male", "Female", "M", "F"],
            "bmi": [None, 28.0, 31.0, 33.0],
            "sbp": [120, 80, 130, 140],
            "dbp": [80, 120, 85, 90],
            "hypertension": ["Yes", "No", "No", "No"],
            "visit_date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "death_date": ["", "", "", ""],
            "follow_up_days": [30, 40, 50, 60],
        }
    ).to_csv(path, index=False)


def _generate_report(tmp_path) -> str:
    data_path = tmp_path / "contract.csv"
    report_path = tmp_path / "report.md"
    _write_contract_csv(data_path)
    run_audit(data_path, QUESTION, report_path)
    return report_path.read_text(encoding="utf-8")


def test_report_does_not_use_stale_v01_release_language(tmp_path) -> None:
    report = _generate_report(tmp_path)

    forbidden_phrases = [
        "v0.1 audit",
        "v0.1 checks",
        "v0.1 does not fit statistical models",
        "v0.1 supports analysis-readiness review",
    ]
    assert all(phrase not in report for phrase in forbidden_phrases)
    assert "v0.1" not in report


def test_report_does_not_leak_stale_v01_from_warning_text(tmp_path) -> None:
    data_path = tmp_path / "contract.csv"
    report_path = tmp_path / "report.md"
    _write_contract_csv(data_path)

    run_audit(
        data_path,
        "Does BMI cause hypertension after adjusting for age and sex?",
        report_path,
    )
    report = report_path.read_text(encoding="utf-8")

    assert "v0.1" not in report


def test_report_contains_required_v02_sections_in_order(tmp_path) -> None:
    report = _generate_report(tmp_path)
    section_order = [
        "# AI-ready Biomedical Data Audit Report",
        "## 1. User Question",
        "## 2. Executive Summary",
        "## 3. Dataset Overview",
        "## 4. Relevant Variables and Study Design",
        "## 5. Missing Data Summary",
        "## 6. Biomedical Plausibility Warnings",
        "## 7. Statistical Risk Warnings",
        "## 8. Privacy / PII Warnings",
        "## 9. Analysis-readiness Notes",
        "## 10. Iterative Extraction Requests",
        "## 11. Questions for Human Confirmation",
        "## 12. Token-saving Summary",
        "## 13. Limitations and Safety Notes",
    ]

    positions = [report.index(section) for section in section_order]
    assert positions == sorted(positions)


def test_report_contains_token_metric_caveat(tmp_path) -> None:
    report = _generate_report(tmp_path)

    assert "character-count / 4 estimate" in report
    assert "not exact tokenizer output" in report


def test_report_contains_safety_limitations(tmp_path) -> None:
    report = _generate_report(tmp_path).lower()
    required_statements = [
        "not a clinical decision tool",
        "does not diagnose disease",
        "does not recommend treatment",
        "does not fit statistical models",
        "does not clean data",
        "does not replace a statistician or clinical data manager",
        "should not be used with identifiable patient data",
        "do not upload real patient data or direct identifiers to external ai systems",
    ]

    assert all(statement in report for statement in required_statements)


def test_report_contains_iterative_extraction_requests_section(tmp_path) -> None:
    report = _generate_report(tmp_path)

    assert "## 10. Iterative Extraction Requests" in report
    assert "Do not provide raw patient rows or direct identifier values." in report


def test_report_contains_missingness_readiness_summary(tmp_path) -> None:
    report = _generate_report(tmp_path)

    assert "### Key-variable complete-case readiness" in report
    assert "### Row-level missingness burden" in report
    assert "### Missingness co-occurrence screening" in report
    assert "### Missingness mechanism screening caveat" in report


def test_report_priority_findings_are_limited() -> None:
    warnings = [
        {
            "issue_id": f"MED_{index:03d}",
            "issue_type": "medical_plausibility",
            "severity": "high",
            "variable": "bmi",
            "count": 1,
            "example_rows": [index],
            "description": f"Synthetic finding {index}.",
            "recommended_action": "Review the source record.",
            "human_confirmation_required": True,
        }
        for index in range(8)
    ]
    report = generate_markdown_report(
        question=QUESTION,
        profile={
            "n_rows": 8,
            "n_columns": 2,
            "variable_types": {"bmi": "numeric", "hypertension": "categorical"},
            "potential_id_columns": [],
            "duplicates": {},
            "missing_summary": {},
            "missingness_readiness": {},
            "categorical_summary": {"hypertension": {"Yes": 4, "No": 4}},
        },
        variable_roles={
            "exposure": ["bmi"],
            "outcome": ["hypertension"],
            "confounders": [],
        },
        medical_warnings=warnings,
    )
    priority_block = report.split("**Priority findings**", 1)[1].split(
        "## 3. Dataset Overview", 1
    )[0]

    assert priority_block.count("\n- `MED_") == 6


def test_report_extraction_requests_are_limited() -> None:
    requests = [
        {
            "priority": "high",
            "request_type": "confirm_metadata",
            "related_variables": [f"variable_{index}"],
            "question": f"Request number {index} END",
            "safe_response_guidance": "Provide metadata only; do not provide raw patient rows.",
        }
        for index in range(12)
    ]

    rendered = render_extraction_requests(requests)

    assert "Request number 9 END" in rendered
    assert "Request number 10 END" not in rendered
    assert "Request number 11 END" not in rendered


def test_report_does_not_include_raw_rows_from_synthetic_data(tmp_path) -> None:
    report = _generate_report(tmp_path)

    forbidden_raw_values = [
        "Synthetic A",
        "Synthetic B",
        "111-111-1111",
        "222-222-2222",
        "P1",
        "P2",
    ]
    assert all(value not in report for value in forbidden_raw_values)
