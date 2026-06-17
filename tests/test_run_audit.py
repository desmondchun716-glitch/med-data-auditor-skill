from __future__ import annotations

import pandas as pd

from conftest import load_script


run_mod = load_script("run_audit_test", "scripts/run_audit.py")


def test_run_audit_writes_required_report_sections(tmp_path) -> None:
    data_path = tmp_path / "mini.csv"
    output_path = tmp_path / "audit.md"
    pd.DataFrame(
        {
            "patient_id": ["P1", "P1", "P2", "P3"],
            "patient_name": ["Synthetic A", "Synthetic A", "Synthetic B", "Synthetic C"],
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
    ).to_csv(data_path, index=False)

    run_mod.run_audit(
        data_path,
        "Is BMI associated with hypertension after adjusting for age and sex?",
        output_path,
    )

    report = output_path.read_text(encoding="utf-8")
    assert "# AI-ready Biomedical Data Audit Report" in report
    assert "Executive Summary" in report
    assert "Readiness verdict" in report
    assert "Biomedical Plausibility Warnings" in report
    assert "Statistical Risk Warnings" in report
    assert "Privacy / PII Warnings" in report
    assert "Analysis-readiness Notes" in report
