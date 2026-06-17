from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


DEFAULT_DICTIONARY = Path(__file__).resolve().parents[1] / "rules" / "variable_dictionary.yaml"


def _load_yaml(path: str | Path | None, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    if fallback is not None:
        return fallback
    with Path(path or DEFAULT_DICTIONARY).open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _contains_term(question: str, term: str) -> bool:
    term = term.lower().strip()
    if not term:
        return False
    if re.fullmatch(r"[a-z0-9_]+", term):
        return re.search(rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])", question) is not None
    return term in question


def identify_relevant_variables(
    question: str,
    columns: list[str],
    dictionary_path: str | Path | None = None,
    dictionary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    variable_dictionary = _load_yaml(dictionary_path, dictionary)
    normalized_question = question.lower()
    column_lookup = {column.lower(): column for column in columns}

    roles = {
        "exposure": [],
        "outcome": [],
        "confounders": [],
        "suggested_confounders": [],
        "uncertain_variables": [],
        "unavailable_variables": [],
    }

    matched: set[str] = set()
    for variable, config in variable_dictionary.items():
        synonyms = [variable] + list(config.get("synonyms", []) or [])
        if not any(_contains_term(normalized_question, synonym) for synonym in synonyms):
            continue
        matched.add(variable)
        actual_column = column_lookup.get(variable.lower())
        if actual_column is None:
            roles["unavailable_variables"].append(variable)
            continue
        role = config.get("default_role", "uncertain")
        if role == "confounder":
            target = "confounders"
        elif role in {"exposure", "outcome"}:
            target = role
        else:
            target = "uncertain_variables"
        if actual_column not in roles[target]:
            roles[target].append(actual_column)

    # Fallback: match literal column names mentioned in the question.
    for column in columns:
        if column in roles["exposure"] + roles["outcome"] + roles["confounders"]:
            continue
        if _contains_term(normalized_question, column.lower()):
            roles["uncertain_variables"].append(column)

    for variable, config in variable_dictionary.items():
        if config.get("default_role") != "confounder":
            continue
        actual_column = column_lookup.get(variable.lower())
        if actual_column is None:
            continue
        already_used = actual_column in roles["confounders"] or actual_column in roles["exposure"] or actual_column in roles["outcome"]
        if not already_used and actual_column not in roles["suggested_confounders"]:
            roles["suggested_confounders"].append(actual_column)

    roles["matched_dictionary_variables"] = sorted(matched)
    return roles
