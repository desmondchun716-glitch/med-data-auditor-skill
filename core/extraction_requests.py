from __future__ import annotations

import re
from collections import defaultdict
from typing import Any


REQUEST_FIELDS = {
    "request_id",
    "priority",
    "request_type",
    "trigger_source",
    "related_variables",
    "related_issue_ids",
    "question",
    "why_needed",
    "expected_response",
    "safe_response_guidance",
    "human_confirmation_required",
}

VALID_PRIORITIES = {"blocker", "high", "medium", "low"}
VALID_REQUEST_TYPES = {
    "confirm_variable_role",
    "provide_data_dictionary",
    "confirm_units",
    "confirm_missingness_handling",
    "confirm_study_design",
    "provide_additional_variables",
    "confirm_privacy_handling",
    "confirm_outcome_definition",
    "confirm_population",
    "confirm_time_window",
    "confirm_repeated_measures",
}
VALID_TRIGGER_SOURCES = {
    "user_question",
    "variable_mapping",
    "study_design",
    "medical_warning",
    "unit_warning",
    "statistical_warning",
    "missingness_readiness",
    "privacy_warning",
    "profile",
}
VALID_EXPECTED_RESPONSES = {
    "yes_no",
    "short_text",
    "column_name_list",
    "data_dictionary_excerpt",
    "unit_definition",
    "coding_dictionary",
    "study_design_metadata",
    "missingness_code_policy",
    "deidentification_policy",
    "analysis_population_definition",
    "time_window_definition",
}

_PRIORITY_ORDER = {"blocker": 0, "high": 1, "medium": 2, "low": 3}
_CATEGORY_ORDER = {
    "PRIVACY": 0,
    "VAR_ROLE": 1,
    "STUDY_DESIGN": 2,
    "UNIT": 3,
    "MISSINGNESS": 4,
    "OUTCOME": 5,
    "ADDITIONAL_VAR": 6,
    "REPEATED": 7,
    "POPULATION": 8,
    "TIME_WINDOW": 9,
    "DATA_DICTIONARY": 10,
}
_REQUEST_ID_PATTERN = re.compile(r"^EXT_[A-Z0-9_]+_\d{3}$")
_CAUSAL_TERMS = {"cause", "causes", "causal", "effect", "impact", "lead to", "reduce", "prevent"}
_TIME_TERMS = {"survival", "follow-up", "follow up", "longitudinal", "cohort", "time to event"}
_NON_VARIABLE_LABELS = {"dataset", "research_question", "none", ""}
_BASE_SAFE_GUIDANCE = "Do not provide raw patient rows or direct identifier values."


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, (list, tuple, set)) else [value]
    result: list[str] = []
    for item in values:
        if not isinstance(item, str):
            continue
        text = item.strip().strip("`")
        if text and text not in result:
            result.append(text)
    return result


def _warning_variables(warnings: list[dict[str, Any]]) -> list[str]:
    variables: list[str] = []
    for warning in warnings:
        value = warning.get("variable")
        if not isinstance(value, str):
            continue
        for item in value.split(","):
            variable = item.strip().strip("`")
            if variable.lower() in _NON_VARIABLE_LABELS or variable in variables:
                continue
            variables.append(variable)
    return sorted(variables)


def _issue_ids(warnings: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            str(warning.get("issue_id")).strip()
            for warning in warnings
            if isinstance(warning.get("issue_id"), str) and str(warning.get("issue_id")).strip()
        }
    )


def _format_variables(variables: list[str]) -> str:
    return ", ".join(f"`{variable}`" for variable in variables)


def _safe_guidance(extra: str) -> str:
    return f"{_BASE_SAFE_GUIDANCE} {extra}".strip()


def _make_candidate(
    *,
    category: str,
    priority: str,
    request_type: str,
    trigger_source: str,
    related_variables: list[str] | None,
    related_issue_ids: list[str] | None,
    question: str,
    why_needed: str,
    expected_response: str,
    safe_response_guidance: str,
) -> dict[str, Any]:
    return {
        "_category": category,
        "priority": priority,
        "request_type": request_type,
        "trigger_source": trigger_source,
        "related_variables": _string_list(related_variables),
        "related_issue_ids": _string_list(related_issue_ids),
        "question": question.strip(),
        "why_needed": why_needed.strip(),
        "expected_response": expected_response,
        "safe_response_guidance": safe_response_guidance.strip(),
        "human_confirmation_required": True,
    }


def _warning_groups(warnings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {
        "unit": [],
        "missingness": [],
        "privacy": [],
        "study_design": [],
        "outcome": [],
        "repeated": [],
        "time": [],
        "coding": [],
    }
    for warning in warnings:
        issue_id = str(warning.get("issue_id", "")).upper()
        issue_type = str(warning.get("issue_type", "")).lower()
        variable = str(warning.get("variable", "")).lower()

        if issue_id.startswith("UNIT_"):
            groups["unit"].append(warning)
        if issue_id.startswith("MISS_"):
            groups["missingness"].append(warning)
        if issue_type == "privacy_risk" or issue_id.startswith(("PRIV_", "PRIVACY_")):
            groups["privacy"].append(warning)
        if issue_type == "study_design" or issue_id.startswith("DESIGN_"):
            groups["study_design"].append(warning)
        if issue_id.startswith(("STAT_OUTCOME_", "STAT_FEW_OUTCOME_EVENTS_", "DESIGN_OUTCOME_")):
            groups["outcome"].append(warning)
        if "DUPLICATE_PATIENT_ID" in issue_id:
            groups["repeated"].append(warning)
        if (
            any(term in issue_id for term in ("DATE", "FOLLOW_UP", "SURVIVAL_TIME"))
            or any(term in variable for term in ("date", "follow_up", "follow-up", "time"))
        ):
            groups["time"].append(warning)
        if "CODING" in issue_id:
            groups["coding"].append(warning)
    return groups


def build_extraction_requests(
    *,
    question: str,
    profile: dict[str, Any],
    variable_roles: dict[str, Any],
    study_design: dict[str, Any],
    warnings: list[dict[str, Any]],
    max_requests: int = 10,
) -> list[dict[str, Any]]:
    """Build deterministic, privacy-safe next-step requests without accessing raw rows."""
    if max_requests <= 0:
        return []

    warning_items = [warning for warning in warnings if isinstance(warning, dict)]
    groups = _warning_groups(warning_items)
    candidates: list[dict[str, Any]] = []

    if not variable_roles.get("exposure"):
        candidates.append(
            _make_candidate(
                category="VAR_ROLE",
                priority="blocker",
                request_type="confirm_variable_role",
                trigger_source="variable_mapping",
                related_variables=[],
                related_issue_ids=[],
                question="Which column is the primary exposure or predictor for the research question?",
                why_needed="The exposure must be identified before analysis readiness can be assessed.",
                expected_response="column_name_list",
                safe_response_guidance=_safe_guidance("Provide column names only."),
            )
        )

    if not variable_roles.get("outcome"):
        candidates.append(
            _make_candidate(
                category="VAR_ROLE",
                priority="blocker",
                request_type="confirm_variable_role",
                trigger_source="variable_mapping",
                related_variables=[],
                related_issue_ids=_issue_ids(groups["outcome"]),
                question="Which column is the outcome variable for the research question?",
                why_needed="The outcome must be identified before its definition, coding, and readiness can be reviewed.",
                expected_response="column_name_list",
                safe_response_guidance=_safe_guidance("Provide column names only."),
            )
        )

    unavailable_variables = sorted(_string_list(variable_roles.get("unavailable_variables")))
    if unavailable_variables:
        candidates.append(
            _make_candidate(
                category="ADDITIONAL_VAR",
                priority="high",
                request_type="provide_additional_variables",
                trigger_source="variable_mapping",
                related_variables=unavailable_variables,
                related_issue_ids=[],
                question=(
                    "The research question mentions variables not found in the CSV. "
                    "Provide the matching de-identified column names or confirm they are unavailable."
                ),
                why_needed="Unavailable variables may change the feasible analysis and adjustment plan.",
                expected_response="column_name_list",
                safe_response_guidance=_safe_guidance(
                    "Provide column names or a de-identified data dictionary excerpt only."
                ),
            )
        )

    if groups["privacy"]:
        candidates.append(
            _make_candidate(
                category="PRIVACY",
                priority="blocker",
                request_type="confirm_privacy_handling",
                trigger_source="privacy_warning",
                related_variables=_warning_variables(groups["privacy"]),
                related_issue_ids=_issue_ids(groups["privacy"]),
                question=(
                    "Please confirm that direct identifiers are removed, hashed, generalized, "
                    "or handled under an approved privacy policy before external AI use."
                ),
                why_needed="Privacy risks must be resolved before data or derived evidence is shared externally.",
                expected_response="deidentification_policy",
                safe_response_guidance=_safe_guidance(
                    "Do not provide names, phone numbers, emails, addresses, notes, screenshots, or full extracts."
                ),
            )
        )

    question_lower = question.lower()
    asks_causal = any(term in question_lower for term in _CAUSAL_TERMS)
    study_confidence = str(study_design.get("confidence", "")).lower()
    study_uncertain = study_confidence in {"", "low", "unknown", "not assessed"}
    if study_uncertain or groups["study_design"] or asks_causal:
        candidates.append(
            _make_candidate(
                category="STUDY_DESIGN",
                priority="high",
                request_type="confirm_study_design",
                trigger_source="study_design" if study_uncertain or groups["study_design"] else "user_question",
                related_variables=_warning_variables(groups["study_design"]),
                related_issue_ids=_issue_ids(groups["study_design"]),
                question=(
                    "Please confirm whether the data are cross-sectional, cohort, case-control, "
                    "trial, repeated-measures, or another design."
                ),
                why_needed="Study design determines which comparisons and interpretations are defensible.",
                expected_response="study_design_metadata",
                safe_response_guidance=_safe_guidance("Provide protocol or design metadata only."),
            )
        )

    if groups["unit"]:
        unit_variables = _warning_variables(groups["unit"])
        variable_text = f" for {_format_variables(unit_variables)}" if unit_variables else ""
        candidates.append(
            _make_candidate(
                category="UNIT",
                priority="high",
                request_type="confirm_units",
                trigger_source="unit_warning",
                related_variables=unit_variables,
                related_issue_ids=_issue_ids(groups["unit"]),
                question=f"Please confirm the intended measurement units{variable_text} before analysis.",
                why_needed="Possible scale or unit mismatches can invalidate plausibility checks and later analysis.",
                expected_response="unit_definition",
                safe_response_guidance=_safe_guidance("Provide unit definitions or source documentation only."),
            )
        )

    missingness_metrics = profile.get("missingness_readiness") or {}
    readiness_flags = _string_list(missingness_metrics.get("readiness_flags"))
    if groups["missingness"] or readiness_flags:
        missing_variables = _warning_variables(groups["missingness"])
        missing_variables.extend(
            variable
            for variable in _string_list(missingness_metrics.get("key_variables_with_missingness"))
            if variable not in missing_variables
        )
        severe_missingness = any(
            str(warning.get("severity", "")).lower() in {"critical", "high"}
            for warning in groups["missingness"]
        ) or any(flag in {"complete_case_rate_low", "key_variable_missingness_high"} for flag in readiness_flags)
        candidates.append(
            _make_candidate(
                category="MISSINGNESS",
                priority="high" if severe_missingness else "medium",
                request_type="confirm_missingness_handling",
                trigger_source="missingness_readiness",
                related_variables=missing_variables,
                related_issue_ids=_issue_ids(groups["missingness"]),
                question=(
                    "Please confirm whether missing values mean not collected, not applicable, "
                    "unknown, refused, or structurally missing."
                ),
                why_needed="Missing-value meanings and collection patterns affect the valid analysis population.",
                expected_response="missingness_code_policy",
                safe_response_guidance=_safe_guidance(
                    "Provide coding rules and collection policy only; do not fill, impute, or paste values."
                ),
            )
        )

    outcomes = _string_list(variable_roles.get("outcome"))
    categorical_summary = profile.get("categorical_summary") or {}
    variable_types = profile.get("variable_types") or {}
    categorical_outcomes = [
        outcome
        for outcome in outcomes
        if outcome in categorical_summary or variable_types.get(outcome) == "categorical"
    ]
    if outcomes and (categorical_outcomes or groups["outcome"]):
        outcome_text = f" for {_format_variables(outcomes)}" if outcomes else ""
        candidates.append(
            _make_candidate(
                category="OUTCOME",
                priority="high",
                request_type="confirm_outcome_definition",
                trigger_source="statistical_warning" if groups["outcome"] else "profile",
                related_variables=outcomes,
                related_issue_ids=_issue_ids(groups["outcome"]),
                question=(
                    f"Please confirm the outcome definition and coding{outcome_text}, "
                    "including which code represents the event."
                ),
                why_needed="Outcome coding must be unambiguous before event counts or model readiness are interpreted.",
                expected_response="coding_dictionary",
                safe_response_guidance=_safe_guidance("Provide the coding dictionary only."),
            )
        )

    duplicate_count = int((profile.get("duplicates") or {}).get("duplicate_patient_id") or 0)
    repeated_evidence = bool(
        groups["repeated"] or duplicate_count > 0 or study_design.get("has_repeated_patient_ids")
    )
    if repeated_evidence:
        repeated_variables = _warning_variables(groups["repeated"]) or ["patient_id"]
        candidates.append(
            _make_candidate(
                category="REPEATED",
                priority="high",
                request_type="confirm_repeated_measures",
                trigger_source="medical_warning" if groups["repeated"] else "profile",
                related_variables=repeated_variables,
                related_issue_ids=_issue_ids(groups["repeated"]),
                question=(
                    "Please confirm whether repeated patient IDs represent duplicate records, repeated visits, "
                    "multiple measurements, or longitudinal follow-up."
                ),
                why_needed="The row-to-person relationship determines independence, clustering, and record handling.",
                expected_response="short_text",
                safe_response_guidance=_safe_guidance("Describe the record structure without listing patient IDs."),
            )
        )

    time_variables = sorted(_string_list(list((profile.get("date_summary") or {}).keys())))
    has_time_evidence = bool(
        time_variables
        or groups["time"]
        or study_design.get("has_time_variable")
        or any(term in question_lower for term in _TIME_TERMS)
    )
    if groups["missingness"] or readiness_flags or study_uncertain or groups["time"]:
        population_issue_ids = _issue_ids(groups["missingness"] + groups["time"] + groups["study_design"])
        candidates.append(
            _make_candidate(
                category="POPULATION",
                priority="medium",
                request_type="confirm_population",
                trigger_source=(
                    "missingness_readiness"
                    if readiness_flags and not study_uncertain
                    else "study_design"
                    if study_uncertain
                    else "profile"
                ),
                related_variables=_warning_variables(groups["missingness"] + groups["time"]),
                related_issue_ids=population_issue_ids,
                question="Please confirm the intended analysis population and any inclusion or exclusion criteria.",
                why_needed="Population rules are needed to interpret completeness, follow-up, and generalizability.",
                expected_response="analysis_population_definition",
                safe_response_guidance=_safe_guidance("Provide eligibility rules or aggregate counts only."),
            )
        )

    if has_time_evidence:
        time_related_variables = list(time_variables)
        time_related_variables.extend(
            variable
            for variable in _warning_variables(groups["time"])
            if variable not in time_related_variables
        )
        high_time_priority = any(
            str(warning.get("severity", "")).lower() in {"critical", "high"} for warning in groups["time"]
        )
        candidates.append(
            _make_candidate(
                category="TIME_WINDOW",
                priority="high" if high_time_priority else "medium",
                request_type="confirm_time_window",
                trigger_source="medical_warning" if groups["time"] else "profile",
                related_variables=time_related_variables,
                related_issue_ids=_issue_ids(groups["time"]),
                question="Please confirm the index date, follow-up window, and outcome ascertainment period.",
                why_needed="Time ordering and observation windows are required for longitudinal or event-based analyses.",
                expected_response="time_window_definition",
                safe_response_guidance=_safe_guidance("Provide date-field definitions and window rules only."),
            )
        )

    uncertain_variables = _string_list(variable_roles.get("uncertain_variables"))
    dictionary_warnings = groups["unit"] + groups["coding"] + groups["outcome"]
    if uncertain_variables or dictionary_warnings:
        dictionary_variables = list(uncertain_variables)
        dictionary_variables.extend(
            variable
            for variable in _warning_variables(dictionary_warnings)
            if variable not in dictionary_variables
        )
        candidates.append(
            _make_candidate(
                category="DATA_DICTIONARY",
                priority="medium",
                request_type="provide_data_dictionary",
                trigger_source="variable_mapping" if uncertain_variables else "profile",
                related_variables=dictionary_variables,
                related_issue_ids=_issue_ids(dictionary_warnings),
                question=(
                    "Please provide a de-identified data dictionary for the key variables, "
                    "including definitions, allowed codes, and units."
                ),
                why_needed="A data dictionary resolves ambiguous meanings without exposing patient-level records.",
                expected_response="data_dictionary_excerpt",
                safe_response_guidance=_safe_guidance("Provide metadata excerpts only."),
            )
        )

    deduplicated: list[dict[str, Any]] = []
    seen_keys: set[tuple[Any, ...]] = set()
    for candidate in candidates:
        dedupe_key = (
            candidate["request_type"],
            tuple(candidate["related_variables"]),
            tuple(candidate["related_issue_ids"]),
            candidate["question"],
        )
        if dedupe_key not in seen_keys:
            seen_keys.add(dedupe_key)
            deduplicated.append(candidate)

    deduplicated.sort(
        key=lambda item: (
            _PRIORITY_ORDER[item["priority"]],
            _CATEGORY_ORDER[item["_category"]],
            item["question"],
        )
    )

    category_counts: dict[str, int] = defaultdict(int)
    requests: list[dict[str, Any]] = []
    for candidate in deduplicated[:max_requests]:
        category = str(candidate.pop("_category"))
        category_counts[category] += 1
        request = {
            "request_id": f"EXT_{category}_{category_counts[category]:03d}",
            **candidate,
        }
        requests.append(request)

    if not validate_extraction_requests_schema(requests):
        raise ValueError("Generated extraction requests do not match the WS6 schema.")
    return requests


def validate_extraction_request_schema(request: dict[str, Any]) -> bool:
    if set(request.keys()) != REQUEST_FIELDS:
        return False
    if not isinstance(request.get("request_id"), str) or not _REQUEST_ID_PATTERN.fullmatch(
        request["request_id"]
    ):
        return False
    if request.get("priority") not in VALID_PRIORITIES:
        return False
    if request.get("request_type") not in VALID_REQUEST_TYPES:
        return False
    if request.get("trigger_source") not in VALID_TRIGGER_SOURCES:
        return False
    if request.get("expected_response") not in VALID_EXPECTED_RESPONSES:
        return False
    for field in ("related_variables", "related_issue_ids"):
        values = request.get(field)
        if not isinstance(values, list) or not all(isinstance(value, str) and value for value in values):
            return False
    for field in ("question", "why_needed", "safe_response_guidance"):
        if not isinstance(request.get(field), str) or not request[field].strip():
            return False
    return request.get("human_confirmation_required") is True


def validate_extraction_requests_schema(requests: list[dict[str, Any]]) -> bool:
    if not isinstance(requests, list):
        return False
    if not all(isinstance(request, dict) and validate_extraction_request_schema(request) for request in requests):
        return False
    request_ids = [request["request_id"] for request in requests]
    return len(request_ids) == len(set(request_ids))
