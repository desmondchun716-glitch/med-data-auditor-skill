from __future__ import annotations

import csv

import pandas as pd

from core.flagged_records import (
    FLAGGED_RECORDS_SCHEMA_VERSION,
    FLAGGED_RECORD_FIELDS,
    build_flagged_records,
    save_flagged_records,
    sanitize_flagged_record_text,
)
from core.orchestrator import run_audit


QUESTION = "Is BMI associated with hypertension after adjusting for age and sex?"


def _warning(example_rows=None) -> dict:
    return {
        "issue_id": "MED_RANGE_BMI",
        "issue_type": "medical_plausibility",
        "severity": "high",
        "variable": "bmi",
        "count": 2,
        "example_rows": example_rows or [],
        "description": "BMI has values outside the plausible adult range.",
        "recommended_action": "Confirm values before analysis.",
        "human_confirmation_required": True,
    }


def _write_demo_csv(path) -> None:
    pd.DataFrame(
        {
            "patient_id": ["P1", "P1", "P2", "P3"],
            "patient_name": ["Alice Private Test", "Alice Private Test", "Bob Private Test", "Carol Private Test"],
            "phone": ["123-456-7890", "123-456-7890", "999-111-2222", "888-333-4444"],
            "age": [150, 40, 50, 60],
            "sex": ["Male", "Female", "M", "F"],
            "bmi": [999.0, 28.0, 31.0, 33.0],
            "sbp": [120, 80, 130, 140],
            "dbp": [80, 120, 85, 90],
            "hypertension": ["Yes", "No", "No", "No"],
            "visit_date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "death_date": ["", "", "", ""],
            "follow_up_days": [30, 40, 50, 60],
            "lab_marker": ["UNIQUE_RAW_CELL_ABC", "UNIQUE_RAW_CELL_DEF", "UNIQUE_RAW_CELL_GHI", "UNIQUE_RAW_CELL_JKL"],
        }
    ).to_csv(path, index=False)


def test_build_flagged_records_one_row_per_example_row() -> None:
    records = build_flagged_records([_warning(example_rows=[7, 19])])

    assert len(records) == 2
    assert records[0]["schema_version"] == FLAGGED_RECORDS_SCHEMA_VERSION
    assert records[0]["row_index"] == 7
    assert records[1]["row_index"] == 19
    assert records[0]["source_warning_count"] == 2
    assert records[0]["human_confirmation_required"] == "true"


def test_build_flagged_records_skips_warnings_without_example_rows() -> None:
    assert build_flagged_records([_warning(example_rows=[])]) == []


def test_save_flagged_records_writes_exact_csv_header(tmp_path) -> None:
    records = build_flagged_records([_warning(example_rows=[7])])
    output_path = tmp_path / "flagged_records.csv"

    save_flagged_records(records, output_path)

    with output_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        assert next(reader) == FLAGGED_RECORD_FIELDS


def test_flagged_records_redacts_direct_identifiers_from_warning_text() -> None:
    warning = _warning(example_rows=[3])
    warning["description"] = "Patient email john@example.com and phone 555-123-4567 appeared."
    warning["recommended_action"] = "Do not expose MRN 123456789012 or sk-test-secretvalue123."

    records = build_flagged_records([warning])
    text = str(records[0])

    assert "john@example.com" not in text
    assert "555-123-4567" not in text
    assert "123456789012" not in text
    assert "sk-test-secretvalue123" not in text
    assert "[REDACTED_EMAIL]" in text
    assert "[REDACTED_PHONE]" in text
    assert "[REDACTED_ID]" in text
    assert "[REDACTED_SECRET]" in text


def test_sanitizer_keeps_safe_text_unchanged() -> None:
    assert sanitize_flagged_record_text("BMI has values outside plausible range.") == "BMI has values outside plausible range."


def test_run_audit_does_not_write_flagged_records_by_default(tmp_path) -> None:
    data_path = tmp_path / "demo.csv"
    report_path = tmp_path / "report.md"
    flagged_records_path = tmp_path / "flagged_records.csv"
    _write_demo_csv(data_path)

    summary = run_audit(data_path, QUESTION, report_path)

    assert report_path.exists()
    assert not flagged_records_path.exists()
    assert summary["flagged_records_path"] is None
    assert summary["flagged_records_count"] is None


def test_run_audit_writes_privacy_safe_flagged_records_when_requested(tmp_path) -> None:
    data_path = tmp_path / "demo.csv"
    report_path = tmp_path / "report.md"
    flagged_records_path = tmp_path / "flagged_records.csv"
    _write_demo_csv(data_path)

    summary = run_audit(data_path, QUESTION, report_path, flagged_records_output_path=flagged_records_path)

    assert flagged_records_path.exists()
    assert summary["flagged_records_path"] == str(flagged_records_path)
    assert summary["flagged_records_count"] and summary["flagged_records_count"] > 0

    with flagged_records_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == FLAGGED_RECORD_FIELDS
        rows = list(reader)

    assert rows
    assert all(row["row_index"] for row in rows)

    text = flagged_records_path.read_text(encoding="utf-8")
    assert "Alice Private Test" not in text
    assert "Bob Private Test" not in text
    assert "Carol Private Test" not in text
    assert "123-456-7890" not in text
    assert "999-111-2222" not in text
    assert "UNIQUE_RAW_CELL_ABC" not in text
    assert "UNIQUE_RAW_CELL_DEF" not in text
