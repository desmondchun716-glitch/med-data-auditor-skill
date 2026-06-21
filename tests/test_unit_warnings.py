from __future__ import annotations

import csv
import json

import pandas as pd
import pytest

from core.orchestrator import run_audit
from core.schemas import validate_warning_schema
from core.unit_warnings import check_unit_warnings


QUESTION = "Is BMI associated with hypertension after adjusting for age and sex?"


def _issue_ids(df: pd.DataFrame) -> set[str]:
    return {warning["issue_id"] for warning in check_unit_warnings(df)}


def test_unit_warnings_validate_audit_warning_schema() -> None:
    warnings = check_unit_warnings(
        pd.DataFrame(
            {
                "sbp": [16, 18, 20],
                "dbp": [10, 11, 12],
                "temperature_c": [98.6, 99.1, 101.0],
                "adherence_percent": [0.8, 0.9, 0.75],
            }
        )
    )

    assert warnings
    assert all(validate_warning_schema(warning) for warning in warnings)
    assert all(warning["issue_type"] == "medical_plausibility" for warning in warnings)
    assert all(warning["issue_id"].startswith("UNIT_") for warning in warnings)
    assert all(warning["human_confirmation_required"] is True for warning in warnings)


def test_unit_warnings_do_not_mutate_dataframe() -> None:
    df = pd.DataFrame(
        {
            "temperature_c": [98.6, 99.1, 101.0],
            "adherence_percent": [0.8, 0.9, 0.75],
        }
    )
    original = df.copy(deep=True)

    check_unit_warnings(df)

    pd.testing.assert_frame_equal(df, original)


def test_blood_pressure_possible_kpa_warning() -> None:
    warnings = check_unit_warnings(pd.DataFrame({"sbp": [16, 18, 20], "dbp": [10, 11, 12]}))
    warning = next(item for item in warnings if item["issue_id"] == "UNIT_BP_POSSIBLE_KPA")

    assert warning["count"] == 3
    assert warning["example_rows"] == [0, 1, 2]
    assert warning["variable"] == "sbp, dbp"
    assert "possible" in warning["description"].lower()
    assert "do not convert automatically" in warning["recommended_action"].lower()
    assert all(raw_value not in warning["description"] for raw_value in ("16", "18", "20"))


@pytest.mark.parametrize(
    ("column", "values"),
    [
        ("temperature_c", [98.6, 99.1, 101.0]),
        ("temperature_f", [36.8, 37.2, 38.0]),
    ],
)
def test_temperature_fahrenheit_celsius_mismatch(column: str, values: list[float]) -> None:
    assert "UNIT_TEMPERATURE_F_C_MISMATCH" in _issue_ids(pd.DataFrame({column: values}))


def test_percent_fraction_mismatch() -> None:
    assert "UNIT_PERCENT_FRACTION_MISMATCH" in _issue_ids(
        pd.DataFrame({"adherence_percent": [0.8, 0.9, 0.75]})
    )
    assert "UNIT_PERCENT_FRACTION_MISMATCH" in _issue_ids(
        pd.DataFrame({"coverage_proportion": [75, 80, 90]})
    )


@pytest.mark.parametrize(
    ("column", "values", "expected_issue"),
    [
        ("height_m", [165, 172, 180], "UNIT_HEIGHT_CM_AS_M"),
        ("height_cm", [1.65, 1.72, 1.80], "UNIT_HEIGHT_M_AS_CM"),
        ("weight_kg", [330, 350, 370], "UNIT_WEIGHT_LB_AS_KG"),
        ("glucose_mg_dl", [5.2, 6.1, 7.0], "UNIT_GLUCOSE_MGDL_MMOLL_MISMATCH"),
        ("creatinine_mg_dl", [70, 88, 105], "UNIT_CREATININE_MGDL_UMOL_MISMATCH"),
        ("ldl_mg_dl", [2.1, 3.4, 4.2], "UNIT_LIPID_MGDL_MMOLL_MISMATCH"),
    ],
)
def test_explicit_unit_labels_with_conflicting_scales(
    column: str,
    values: list[float],
    expected_issue: str,
) -> None:
    assert expected_issue in _issue_ids(pd.DataFrame({column: values}))


def test_no_unit_warning_for_normal_sample_values() -> None:
    df = pd.DataFrame(
        {
            "sbp": [120, 130, 118],
            "dbp": [80, 85, 76],
            "bmi": [22, 28, 31],
            "temperature_c": [36.7, 37.0, 38.1],
            "adherence_percent": [80, 90, 75],
            "height_cm": [165, 172, 180],
            "weight_kg": [60, 75, 92],
            "glucose_mg_dl": [90, 110, 126],
            "creatinine_mg_dl": [0.8, 1.0, 1.2],
            "ldl_mg_dl": [90, 120, 145],
        }
    )

    assert check_unit_warnings(df) == []


def test_unit_warnings_flow_into_report_audit_log_and_flagged_records_if_examples_exist(tmp_path) -> None:
    data_path = tmp_path / "unit_demo.csv"
    report_path = tmp_path / "report.md"
    audit_log_path = tmp_path / "audit_log.json"
    flagged_records_path = tmp_path / "flagged_records.csv"
    pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3"],
            "age": [40, 50, 60],
            "sex": ["F", "M", "F"],
            "bmi": [22.0, 27.0, 31.0],
            "sbp": [16, 18, 20],
            "dbp": [10, 11, 12],
            "hypertension": ["No", "No", "Yes"],
        }
    ).to_csv(data_path, index=False)

    run_audit(
        data_path,
        QUESTION,
        report_path,
        audit_log_output_path=audit_log_path,
        flagged_records_output_path=flagged_records_path,
    )

    report_text = report_path.read_text(encoding="utf-8")
    audit_log = json.loads(audit_log_path.read_text(encoding="utf-8"))
    with flagged_records_path.open("r", encoding="utf-8", newline="") as fh:
        flagged_records = list(csv.DictReader(fh))

    assert "UNIT_BP_POSSIBLE_KPA" in report_text
    assert any(item["issue_id"] == "UNIT_BP_POSSIBLE_KPA" for item in audit_log["warnings"]["items"])
    assert any(row["issue_id"] == "UNIT_BP_POSSIBLE_KPA" for row in flagged_records)
