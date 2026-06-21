from __future__ import annotations

import copy
import json

import pandas as pd
from pandas.testing import assert_frame_equal

from core.audit_log import validate_audit_log_schema
from core.flagged_records import build_flagged_records
from core.missingness_readiness import (
    build_missingness_readiness_metrics,
    check_missingness_readiness,
)
from core.orchestrator import run_audit
from core.profiler import profile_dataset
from core.schemas import validate_warning_schema


QUESTION = "Is BMI associated with hypertension after adjusting for age and sex?"
ROLES = {
    "exposure": ["bmi"],
    "outcome": ["hypertension"],
    "confounders": ["age", "sex"],
}


def _readiness_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age": [50, 60, None, 55, 48],
            "bmi": [22.1, None, None, 31.0, 28.5],
            "hypertension": [1, 0, 1, None, 1],
            "sex": ["F", "M", "F", "M", None],
        }
    )


def test_missingness_readiness_metrics_basic_counts() -> None:
    metrics = build_missingness_readiness_metrics(_readiness_df(), ROLES)

    assert metrics["total_rows"] == 5
    assert metrics["total_columns"] == 4
    assert metrics["columns_with_any_missing"] == ["age", "bmi", "hypertension", "sex"]
    assert metrics["rows_with_any_missing"] == 4
    assert metrics["complete_rows_all_columns"] == 1
    assert metrics["overall_missing_cell_rate"] == 0.25
    assert metrics["top_missing_columns"][0] == {
        "column": "bmi",
        "missing_count": 2,
        "missing_rate": 0.4,
    }


def test_missingness_readiness_key_complete_case_rate() -> None:
    metrics = build_missingness_readiness_metrics(_readiness_df(), ROLES)

    assert metrics["key_variables"] == ["bmi", "hypertension", "age", "sex"]
    assert metrics["complete_case_count_for_key_variables"] == 1
    assert metrics["complete_case_rate_for_key_variables"] == 0.2
    assert metrics["rows_missing_any_key_variable"] == 4
    assert metrics["rows_missing_any_key_variable_rate"] == 0.8
    assert set(metrics["key_variables_with_missingness"]) == {"age", "bmi", "hypertension", "sex"}


def test_missingness_readiness_no_dataframe_mutation() -> None:
    df = _readiness_df()
    original = df.copy(deep=True)

    build_missingness_readiness_metrics(df, copy.deepcopy(ROLES))
    check_missingness_readiness(df, copy.deepcopy(ROLES))

    assert_frame_equal(df, original)


def test_missingness_readiness_example_rows_use_safe_positions() -> None:
    df = _readiness_df()
    df.index = ["row-a", "row-b", "row-c", "row-d", "row-e"]

    warnings = check_missingness_readiness(df, ROLES)
    example_rows = [
        row
        for warning in warnings
        for row in warning["example_rows"]
    ]

    assert example_rows
    assert all(isinstance(row, int) for row in example_rows)


def test_missingness_readiness_empty_dataset_has_no_complete_case_claim() -> None:
    df = pd.DataFrame(columns=["bmi", "hypertension", "age", "sex"])

    metrics = build_missingness_readiness_metrics(df, ROLES)
    warnings = check_missingness_readiness(df, ROLES)

    assert metrics["complete_case_rate_for_key_variables"] is None
    assert metrics["rows_missing_any_key_variable_rate"] is None
    assert not any(warning["issue_id"] == "MISS_KEY_COMPLETE_CASE_LOW" for warning in warnings)


def test_missingness_readiness_warning_schema() -> None:
    warnings = check_missingness_readiness(_readiness_df(), ROLES)

    assert warnings
    assert all(warning["issue_id"].startswith("MISS_") for warning in warnings)
    assert all(warning["issue_type"] in {"statistical_risk", "data_quality"} for warning in warnings)
    assert all(validate_warning_schema(warning) for warning in warnings)


def test_missingness_readiness_does_not_classify_mcar_mar_mnar() -> None:
    warnings = check_missingness_readiness(_readiness_df(), ROLES)
    warning_text = " ".join(
        f"{warning['description']} {warning['recommended_action']}" for warning in warnings
    ).lower()

    assert "this is mcar" not in warning_text
    assert "this is mar" not in warning_text
    assert "this is mnar" not in warning_text
    assert "classify missingness" not in warning_text
    assert "review" in warning_text or "confirm" in warning_text


def test_missingness_readiness_cooccurrence_pairs_are_safe() -> None:
    df = pd.DataFrame(
        {
            "lab_a": [None, None, 1, 2, None],
            "lab_b": [None, None, 3, 4, None],
            "outcome": [1, 0, 1, 0, 1],
        }
    )

    metrics = build_missingness_readiness_metrics(df)
    top_pair = metrics["top_missingness_cooccurrence_pairs"][0]

    assert top_pair == {
        "variable_a": "lab_a",
        "variable_b": "lab_b",
        "joint_missing_count": 3,
        "joint_missing_rate": 0.6,
    }
    assert set(top_pair) == {
        "variable_a",
        "variable_b",
        "joint_missing_count",
        "joint_missing_rate",
    }
    assert 1 not in top_pair.values()
    assert 2 not in top_pair.values()
    assert 3 not in [value for key, value in top_pair.items() if key.startswith("variable")]


def test_missingness_readiness_profile_integration() -> None:
    profile = profile_dataset(_readiness_df())

    assert "missingness_readiness" in profile
    assert profile["missingness_readiness"]["total_rows"] == 5
    assert profile["missingness_readiness"]["key_variables"] == []
    assert profile["missingness_readiness"]["complete_case_rate_for_key_variables"] is None


def test_missingness_readiness_audit_log_integration(tmp_path) -> None:
    data_path = tmp_path / "demo.csv"
    report_path = tmp_path / "report.md"
    audit_log_path = tmp_path / "audit_log.json"
    _readiness_df().to_csv(data_path, index=False)

    summary = run_audit(
        data_path,
        QUESTION,
        report_path,
        audit_log_output_path=audit_log_path,
    )
    audit_log = summary["audit_log"]
    metrics = audit_log["dataset_summary"]["missingness_readiness"]

    assert validate_audit_log_schema(audit_log)
    assert metrics["complete_case_rate_for_key_variables"] == 0.2
    assert metrics["key_variables"] == ["bmi", "hypertension", "age", "sex"]
    assert all(not key.startswith("_") for key in metrics)
    assert json.loads(audit_log_path.read_text(encoding="utf-8"))["dataset_summary"][
        "missingness_readiness"
    ] == metrics


def test_missingness_readiness_flagged_records_integration() -> None:
    warnings = check_missingness_readiness(_readiness_df(), ROLES)
    flagged_records = build_flagged_records(warnings)

    assert flagged_records
    assert any(record["issue_id"] == "MISS_KEY_COMPLETE_CASE_LOW" for record in flagged_records)
    assert all(record["row_index"] != "" for record in flagged_records)
    assert all("raw" not in record["safe_evidence_summary"].lower() for record in flagged_records)


def test_missingness_readiness_no_raw_values_in_warnings() -> None:
    sensitive_values = ["UNIQUE_SECRET_ALPHA", "UNIQUE_SECRET_BETA"]
    df = pd.DataFrame(
        {
            "bmi": [None, None, 25.0, 26.0, 27.0],
            "hypertension": [1, None, 0, 1, 0],
            "age": [50, 60, None, 70, 80],
            "sex": sensitive_values + ["F", "M", "F"],
        }
    )

    warning_text = json.dumps(check_missingness_readiness(df, ROLES), ensure_ascii=False)

    assert sensitive_values[0] not in warning_text
    assert sensitive_values[1] not in warning_text


def test_missingness_readiness_report_integration(tmp_path) -> None:
    data_path = tmp_path / "demo.csv"
    report_path = tmp_path / "report.md"
    _readiness_df().to_csv(data_path, index=False)

    run_audit(data_path, QUESTION, report_path)
    report = report_path.read_text(encoding="utf-8")

    assert "Key-variable complete-case readiness" in report
    assert "Row-level missingness burden" in report
    assert "Missingness co-occurrence screening" in report
    assert "does not classify missingness as MCAR, MAR, or MNAR" in report
