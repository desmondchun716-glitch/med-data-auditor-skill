from __future__ import annotations

import json

import pandas as pd

from core.audit_log import AUDIT_LOG_SCHEMA_VERSION, validate_audit_log_schema
from core.orchestrator import run_audit
from core.schemas import REQUIRED_WARNING_FIELDS, validate_warning_schema


QUESTION = "Is BMI associated with hypertension after adjusting for age and sex?"


def _write_demo_csv(path) -> None:
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


def test_build_audit_log_required_keys(tmp_path) -> None:
    data_path = tmp_path / "demo.csv"
    report_path = tmp_path / "report.md"
    audit_log_path = tmp_path / "audit_log.json"
    _write_demo_csv(data_path)

    summary = run_audit(data_path, QUESTION, report_path, audit_log_output_path=audit_log_path)
    audit_log = summary["audit_log"]

    assert audit_log["schema_version"] == AUDIT_LOG_SCHEMA_VERSION
    assert validate_audit_log_schema(audit_log)
    assert set(audit_log) == {
        "schema_version",
        "tool",
        "run",
        "inputs",
        "outputs",
        "dataset_summary",
        "analysis_context",
        "warnings",
        "token_metrics",
        "privacy_safety",
    }
    assert audit_log["dataset_summary"]["row_count"] == 4
    assert audit_log["dataset_summary"]["column_count"] == 12
    assert audit_log["privacy_safety"]["raw_rows_stored"] is False
    assert audit_log["privacy_safety"]["direct_identifier_values_stored"] is False


def test_run_audit_writes_audit_log_json(tmp_path) -> None:
    data_path = tmp_path / "demo.csv"
    report_path = tmp_path / "report.md"
    audit_log_path = tmp_path / "audit_log.json"
    _write_demo_csv(data_path)

    summary = run_audit(data_path, QUESTION, report_path, audit_log_output_path=audit_log_path)

    assert report_path.exists()
    assert audit_log_path.exists()
    assert summary["audit_log_path"] == str(audit_log_path)
    payload = json.loads(audit_log_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == AUDIT_LOG_SCHEMA_VERSION
    assert payload["outputs"]["report_path"] == str(report_path)
    assert payload["outputs"]["audit_log_path"] == str(audit_log_path)


def test_audit_log_does_not_store_raw_pii_values(tmp_path) -> None:
    data_path = tmp_path / "pii_demo.csv"
    data_path.write_text(
        "patient_id,patient_name,phone,age,bmi,hypertension\n"
        "p1,Alice Private Test,123-456-7890,50,25.0,1\n"
        "p2,Bob Private Test,999-111-2222,60,30.0,0\n",
        encoding="utf-8",
    )
    report_path = tmp_path / "report.md"
    audit_log_path = tmp_path / "audit_log.json"

    run_audit(
        data_path,
        "Is BMI associated with hypertension?",
        report_path,
        audit_log_output_path=audit_log_path,
    )

    text = audit_log_path.read_text(encoding="utf-8")
    assert "Alice Private Test" not in text
    assert "Bob Private Test" not in text
    assert "123-456-7890" not in text
    assert "999-111-2222" not in text


def test_existing_warning_items_match_warning_schema(tmp_path) -> None:
    data_path = tmp_path / "demo.csv"
    report_path = tmp_path / "report.md"
    audit_log_path = tmp_path / "audit_log.json"
    _write_demo_csv(data_path)

    summary = run_audit(data_path, QUESTION, report_path, audit_log_output_path=audit_log_path)
    warning_items = summary["audit_log"]["warnings"]["items"]

    assert warning_items
    assert all(set(item.keys()) == REQUIRED_WARNING_FIELDS for item in warning_items)
    assert all(validate_warning_schema(item) for item in warning_items)
