from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .schemas import make_warning


DEFAULT_DICTIONARY = Path(__file__).resolve().parents[1] / "rules" / "variable_dictionary.yaml"
CAUSAL_TERMS = {"cause", "causes", "causal", "effect", "impact", "lead to", "reduce", "prevent"}


def load_variable_dictionary(path: str | Path | None = None) -> dict[str, Any]:
    with Path(path or DEFAULT_DICTIONARY).open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _contains_term(question: str, term: str) -> bool:
    term = term.lower().strip()
    if not term:
        return False
    if re.fullmatch(r"[a-z0-9_]+", term):
        return re.search(rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])", question) is not None
    return term in question


def match_question_terms(question: str, variable_dictionary: dict[str, Any]) -> set[str]:
    normalized_question = question.lower()
    matched: set[str] = set()
    for variable, config in variable_dictionary.items():
        synonyms = [variable] + list(config.get("synonyms", []) or [])
        if any(_contains_term(normalized_question, synonym) for synonym in synonyms):
            matched.add(variable)
    return matched


def match_dataset_columns(columns: list[str], variable_dictionary: dict[str, Any]) -> dict[str, str]:
    column_lookup = {column.lower(): column for column in columns}
    return {variable: column_lookup[variable.lower()] for variable in variable_dictionary if variable.lower() in column_lookup}


def identify_variable_roles(
    question: str,
    columns: list[str],
    variable_dictionary: dict[str, Any] | None = None,
    dictionary_path: str | Path | None = None,
    dictionary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if variable_dictionary is None:
        variable_dictionary = dictionary or load_variable_dictionary(dictionary_path)

    normalized_question = question.lower()
    column_lookup = {column.lower(): column for column in columns}

    roles: dict[str, Any] = {
        "exposure": [],
        "outcome": [],
        "confounders": [],
        "suggested_confounders": [],
        "uncertain_variables": [],
        "unavailable_variables": [],
    }

    matched = match_question_terms(question, variable_dictionary)
    for variable in sorted(matched):
        config = variable_dictionary[variable]
        actual_column = column_lookup.get(variable.lower())
        if actual_column is None:
            roles["unavailable_variables"].append(variable)
            continue
        role = config.get("default_role", "uncertain")
        if role == "confounder":
            target = "confounders"
        elif role == "possible_confounder":
            target = "suggested_confounders"
        elif role in {"exposure", "outcome"}:
            target = role
        else:
            target = "uncertain_variables"
        if actual_column not in roles[target]:
            roles[target].append(actual_column)

    for column in columns:
        already_used = any(column in roles[key] for key in ("exposure", "outcome", "confounders", "suggested_confounders"))
        if not already_used and _contains_term(normalized_question, column.lower()):
            roles["uncertain_variables"].append(column)

    for variable, config in variable_dictionary.items():
        if config.get("default_role") not in {"confounder", "possible_confounder"}:
            continue
        actual_column = column_lookup.get(variable.lower())
        if actual_column is None:
            continue
        already_used = any(actual_column in roles[key] for key in ("confounders", "exposure", "outcome", "suggested_confounders"))
        if not already_used:
            roles["suggested_confounders"].append(actual_column)

    roles["matched_dictionary_variables"] = sorted(matched)
    return roles


def suggest_additional_confounders(variable_roles: dict[str, Any], available_columns: list[str]) -> list[str]:
    common = ["age", "sex", "smoking", "diabetes", "treatment_group"]
    used = set(variable_roles.get("exposure", []) + variable_roles.get("outcome", []) + variable_roles.get("confounders", []))
    return [column for column in common if column in available_columns and column not in used]


def infer_basic_study_design(df: pd.DataFrame, columns: list[str]) -> dict[str, Any]:
    lower_columns = {column.lower() for column in columns}
    has_time = any("date" in column or "time" in column or "follow_up" in column for column in lower_columns)
    has_treatment = any(column in lower_columns for column in {"treatment", "treatment_group", "arm", "group"})
    has_repeated_patient_ids = "patient_id" in lower_columns and df["patient_id"].duplicated().any() if "patient_id" in df.columns else False

    if has_treatment and has_time:
        design = "trial_or_longitudinal_like"
    elif has_time or has_repeated_patient_ids:
        design = "longitudinal_like"
    else:
        design = "cross_sectional_or_unspecified"

    return {
        "inferred_design": design,
        "has_time_variable": bool(has_time),
        "has_treatment_group": bool(has_treatment),
        "has_repeated_patient_ids": bool(has_repeated_patient_ids),
        "confidence": "low",
        "note": "This workflow uses simple column-name heuristics; ask the user to confirm study design.",
    }


def generate_study_design_warnings(
    question: str,
    variable_roles: dict[str, Any],
    study_design: dict[str, Any],
) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    question_lower = question.lower()
    asks_causal = any(term in question_lower for term in CAUSAL_TERMS)

    if study_design.get("inferred_design") == "cross_sectional_or_unspecified":
        warnings.append(
            make_warning(
                "DESIGN_UNSPECIFIED",
                "study_design",
                "medium",
                None,
                "Study design appears cross-sectional or unspecified from available columns.",
                "Confirm whether the dataset is cross-sectional, longitudinal, trial-based, or RWE before interpreting associations.",
                human_confirmation_required=True,
            )
        )

    if asks_causal:
        warnings.append(
            make_warning(
                "DESIGN_CAUSAL_LANGUAGE_RISK",
                "study_design",
                "high",
                None,
                "The user question appears to use causal language, but this workflow cannot confirm causal design support.",
                "Use association language unless study design and analysis plan support causal interpretation.",
                human_confirmation_required=True,
            )
        )

    if not variable_roles.get("outcome"):
        warnings.append(
            make_warning(
                "DESIGN_OUTCOME_UNCLEAR",
                "variable_mapping",
                "high",
                None,
                "No outcome variable was confidently identified from the question.",
                "Ask the user to identify the outcome variable before analysis-readiness advice.",
                human_confirmation_required=True,
            )
        )

    if "survival" in question_lower and not study_design.get("has_time_variable"):
        warnings.append(
            make_warning(
                "DESIGN_SURVIVAL_TIME_MISSING",
                "study_design",
                "high",
                None,
                "The question suggests time-to-event analysis, but no time variable was detected.",
                "Confirm follow-up time, event indicator, and censoring fields before survival analysis.",
                human_confirmation_required=True,
            )
        )

    return warnings


def identify_relevant_variables(
    question: str,
    columns: list[str],
    dictionary_path: str | Path | None = None,
    dictionary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return identify_variable_roles(question, columns, dictionary_path=dictionary_path, dictionary=dictionary)
