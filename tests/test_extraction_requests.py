from __future__ import annotations

import json

import pandas as pd

from core.audit_log import validate_audit_log_schema
from core.extraction_requests import (
    REQUEST_FIELDS,
    build_extraction_requests,
    validate_extraction_request_schema,
    validate_extraction_requests_schema,
)
from core.flagged_records import FLAGGED_RECORD_FIELDS
from core.orchestrator import run_audit


BASE_PROFILE = {
    "columns": ["bmi", "hypertension", "age", "sex"],
    "variable_types": {
        "bmi": "numeric",
        "hypertension": "categorical",
        "age": "numeric",
        "sex": "categorical",
    },
    "categorical_summary": {"hypertension": {"Yes": 40, "No": 60}},
    "date_summary": {},
    "duplicates": {"duplicate_patient_id": 0},
    "missingness_readiness": {"readiness_flags": [], "key_variables_with_missingness": []},
}
BASE_ROLES = {
    "exposure": ["bmi"],
    "outcome": ["hypertension"],
    "confounders": ["age", "sex"],
    "uncertain_variables": [],
    "unavailable_variables": [],
}
BASE_STUDY_DESIGN = {
    "inferred_design": "cross_sectional",
    "confidence": "high",
    "has_time_variable": False,
    "has_repeated_patient_ids": False,
}


def _warning(
    issue_id: str,
    *,
    issue_type: str = "statistical_risk",
    severity: str = "high",
    variable: str | None = "bmi",
    description: str = "Synthetic warning description.",
    recommended_action: str = "Confirm metadata before analysis.",
) -> dict:
    return {
        "issue_id": issue_id,
        "issue_type": issue_type,
        "severity": severity,
        "variable": variable,
        "count": 1,
        "example_rows": [0],
        "description": description,
        "recommended_action": recommended_action,
        "human_confirmation_required": True,
    }


def _build(
    *,
    profile: dict | None = None,
    variable_roles: dict | None = None,
    study_design: dict | None = None,
    warnings: list[dict] | None = None,
    max_requests: int = 10,
) -> list[dict]:
    return build_extraction_requests(
        question="Is BMI associated with hypertension after adjusting for age and sex?",
        profile=profile or BASE_PROFILE,
        variable_roles=variable_roles or BASE_ROLES,
        study_design=study_design or BASE_STUDY_DESIGN,
        warnings=warnings or [],
        max_requests=max_requests,
    )


def _request_of_type(requests: list[dict], request_type: str) -> dict:
    return next(request for request in requests if request["request_type"] == request_type)


def test_extraction_request_schema_validates() -> None:
    requests = _build(variable_roles={**BASE_ROLES, "exposure": []})

    assert requests
    assert set(requests[0]) == REQUEST_FIELDS
    assert validate_extraction_request_schema(requests[0])
    assert validate_extraction_requests_schema(requests)
    assert all(request["human_confirmation_required"] is True for request in requests)
    assert all(request["safe_response_guidance"] for request in requests)


def test_missing_exposure_generates_blocker_request() -> None:
    requests = _build(variable_roles={**BASE_ROLES, "exposure": []})

    request = _request_of_type(requests, "confirm_variable_role")
    assert request["priority"] == "blocker"
    assert "exposure" in request["question"].lower()
    assert request["expected_response"] == "column_name_list"


def test_missing_outcome_generates_blocker_request() -> None:
    requests = _build(variable_roles={**BASE_ROLES, "outcome": []})

    request = _request_of_type(requests, "confirm_variable_role")
    assert request["priority"] == "blocker"
    assert "outcome" in request["question"].lower()
    assert request["expected_response"] == "column_name_list"


def test_unavailable_variables_generate_additional_variable_request() -> None:
    requests = _build(
        variable_roles={**BASE_ROLES, "unavailable_variables": ["smoking_status"]}
    )

    request = _request_of_type(requests, "provide_additional_variables")
    assert request["priority"] == "high"
    assert request["related_variables"] == ["smoking_status"]
    assert request["expected_response"] == "column_name_list"


def test_unit_warnings_generate_grouped_unit_confirmation_request() -> None:
    warnings = [
        _warning("UNIT_BP_POSSIBLE_KPA", issue_type="medical_plausibility", variable="sbp, dbp"),
        _warning(
            "UNIT_GLUCOSE_MGDL_MMOLL_MISMATCH",
            issue_type="medical_plausibility",
            variable="glucose_mg_dl",
        ),
    ]

    requests = _build(warnings=warnings)
    unit_requests = [request for request in requests if request["request_type"] == "confirm_units"]

    assert len(unit_requests) == 1
    assert unit_requests[0]["related_variables"] == ["dbp", "glucose_mg_dl", "sbp"]
    assert unit_requests[0]["related_issue_ids"] == [
        "UNIT_BP_POSSIBLE_KPA",
        "UNIT_GLUCOSE_MGDL_MMOLL_MISMATCH",
    ]
    assert "raw patient rows" in unit_requests[0]["safe_response_guidance"]


def test_missingness_warnings_generate_missingness_policy_request() -> None:
    warning = _warning(
        "MISS_KEY_COMPLETE_CASE_LOW",
        severity="critical",
        variable="bmi, hypertension",
    )

    request = _request_of_type(_build(warnings=[warning]), "confirm_missingness_handling")

    assert request["priority"] == "high"
    assert request["expected_response"] == "missingness_code_policy"
    combined_text = f"{request['question']} {request['why_needed']} {request['safe_response_guidance']}".lower()
    assert "mcar" not in combined_text
    assert "mar" not in combined_text
    assert "mnar" not in combined_text
    assert "impute" in request["safe_response_guidance"].lower()


def test_missingness_readiness_flags_trigger_requests_without_warning() -> None:
    profile = {
        **BASE_PROFILE,
        "missingness_readiness": {
            "readiness_flags": ["complete_case_rate_low"],
            "key_variables_with_missingness": ["bmi"],
        },
    }

    requests = _build(profile=profile)

    missingness_request = _request_of_type(requests, "confirm_missingness_handling")
    population_request = _request_of_type(requests, "confirm_population")
    assert missingness_request["trigger_source"] == "missingness_readiness"
    assert missingness_request["related_variables"] == ["bmi"]
    assert population_request["trigger_source"] == "missingness_readiness"


def test_privacy_warnings_generate_privacy_blocker_request() -> None:
    warning = _warning(
        "PRIVACY_DIRECT_IDENTIFIER_FIELD",
        issue_type="privacy_risk",
        severity="critical",
        variable="patient_name",
    )

    request = _request_of_type(_build(warnings=[warning]), "confirm_privacy_handling")

    assert request["priority"] == "blocker"
    assert request["expected_response"] == "deidentification_policy"
    assert "direct identifier" in request["safe_response_guidance"].lower()


def test_study_design_low_confidence_generates_design_request() -> None:
    requests = _build(study_design={**BASE_STUDY_DESIGN, "confidence": "low"})

    request = _request_of_type(requests, "confirm_study_design")
    assert request["priority"] == "high"
    assert request["trigger_source"] == "study_design"
    assert request["expected_response"] == "study_design_metadata"


def test_duplicate_patient_id_generates_repeated_measures_request() -> None:
    profile = {
        **BASE_PROFILE,
        "duplicates": {"duplicate_patient_id": 4},
    }
    warning = _warning(
        "MED_DUPLICATE_PATIENT_ID",
        issue_type="data_quality",
        severity="critical",
        variable="patient_id",
    )

    request = _request_of_type(
        _build(profile=profile, warnings=[warning]),
        "confirm_repeated_measures",
    )

    assert request["priority"] == "high"
    assert request["related_variables"] == ["patient_id"]
    assert request["related_issue_ids"] == ["MED_DUPLICATE_PATIENT_ID"]


def test_requests_are_deduplicated_deterministic_and_limited() -> None:
    warnings = [
        _warning("UNIT_BP_POSSIBLE_KPA", issue_type="medical_plausibility", variable="sbp, dbp"),
        _warning("UNIT_TEMPERATURE_F_C_MISMATCH", issue_type="medical_plausibility", variable="temperature_c"),
        _warning("MISS_KEY_COMPLETE_CASE_LOW", severity="critical", variable="bmi, hypertension"),
        _warning("PRIV_DIRECT_IDENTIFIER", issue_type="privacy_risk", severity="critical", variable="name"),
        _warning("MED_DUPLICATE_PATIENT_ID", issue_type="data_quality", severity="critical", variable="patient_id"),
    ]
    roles = {
        **BASE_ROLES,
        "exposure": [],
        "outcome": [],
        "unavailable_variables": ["smoking"],
    }
    design = {**BASE_STUDY_DESIGN, "confidence": "low", "has_time_variable": True}

    requests = _build(
        variable_roles=roles,
        study_design=design,
        warnings=warnings,
        max_requests=4,
    )
    reversed_requests = _build(
        variable_roles=roles,
        study_design=design,
        warnings=list(reversed(warnings)),
        max_requests=4,
    )

    assert len(requests) == 4
    assert requests == reversed_requests
    assert len([request for request in requests if request["request_type"] == "confirm_units"]) <= 1
    assert requests[0]["request_type"] == "confirm_privacy_handling"
    assert len({request["request_id"] for request in requests}) == len(requests)


def test_requests_do_not_include_raw_values() -> None:
    sentinel = "UNIQUE_RAW_PATIENT_VALUE_ABC"
    profile = {
        **BASE_PROFILE,
        "categorical_summary": {"hypertension": {sentinel: 1, "other": 2}},
    }
    warning = _warning(
        "STAT_OUTCOME_IMBALANCE_HYPERTENSION",
        variable="hypertension",
        description=f"Raw value {sentinel} appeared.",
        recommended_action=f"Review {sentinel}.",
    )

    requests = _build(
        profile=profile,
        warnings=[warning],
    )

    text = json.dumps(requests)
    assert sentinel not in text
    assert all("raw patient rows" in request["safe_response_guidance"] for request in requests)


def _write_integration_csv(path) -> None:
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
            "lab_marker": [
                "UNIQUE_RAW_CELL_ABC",
                "UNIQUE_RAW_CELL_DEF",
                "UNIQUE_RAW_CELL_GHI",
                "UNIQUE_RAW_CELL_JKL",
            ],
        }
    ).to_csv(path, index=False)


def test_report_includes_iterative_extraction_requests(tmp_path) -> None:
    data_path = tmp_path / "demo.csv"
    report_path = tmp_path / "report.md"
    _write_integration_csv(data_path)

    run_audit(
        data_path,
        "Is BMI associated with hypertension after adjusting for age and sex?",
        report_path,
    )

    report = report_path.read_text(encoding="utf-8")
    assert "## 10. Iterative Extraction Requests" in report
    assert "Do not provide raw patient rows or direct identifier values." in report
    assert "| Priority | Request Type | Related Variables | Request | Safe Response |" in report
    assert "UNIQUE_RAW_CELL_ABC" not in report


def test_audit_log_includes_valid_extraction_requests_under_analysis_context(tmp_path) -> None:
    data_path = tmp_path / "demo.csv"
    report_path = tmp_path / "report.md"
    audit_log_path = tmp_path / "audit_log.json"
    _write_integration_csv(data_path)

    summary = run_audit(
        data_path,
        "Is BMI associated with hypertension after adjusting for age and sex?",
        report_path,
        audit_log_output_path=audit_log_path,
    )
    audit_log = summary["audit_log"]
    requests = audit_log["analysis_context"]["extraction_requests"]

    assert requests
    assert validate_extraction_requests_schema(requests)
    assert validate_audit_log_schema(audit_log)
    assert "extraction_requests" not in audit_log


def test_audit_log_schema_still_validates(tmp_path) -> None:
    data_path = tmp_path / "demo.csv"
    report_path = tmp_path / "report.md"
    audit_log_path = tmp_path / "audit_log.json"
    _write_integration_csv(data_path)

    summary = run_audit(
        data_path,
        "Is BMI associated with hypertension after adjusting for age and sex?",
        report_path,
        audit_log_output_path=audit_log_path,
    )

    assert validate_audit_log_schema(summary["audit_log"])
    assert set(summary["audit_log"]) == {
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


def test_flagged_records_schema_unchanged() -> None:
    assert FLAGGED_RECORD_FIELDS == [
        "schema_version",
        "issue_id",
        "issue_type",
        "severity",
        "variable",
        "row_index",
        "source_warning_count",
        "safe_evidence_summary",
        "recommended_action",
        "human_confirmation_required",
    ]


def test_run_audit_does_not_mutate_source_data(tmp_path) -> None:
    data_path = tmp_path / "demo.csv"
    report_path = tmp_path / "report.md"
    _write_integration_csv(data_path)
    before = data_path.read_bytes()

    run_audit(
        data_path,
        "Is BMI associated with hypertension after adjusting for age and sex?",
        report_path,
    )

    assert data_path.read_bytes() == before
