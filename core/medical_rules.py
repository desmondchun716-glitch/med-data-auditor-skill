from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .schemas import make_warning
from .unit_warnings import check_unit_warnings


DEFAULT_RULES = Path(__file__).resolve().parents[1] / "rules" / "medical_rules.yaml"


def load_medical_rules(path: str | Path | None = None) -> dict[str, Any]:
    with Path(path or DEFAULT_RULES).open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _load_yaml(path: str | Path | None, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    return fallback if fallback is not None else load_medical_rules(path)


def _example_rows(mask: pd.Series, limit: int = 5) -> list[int]:
    return [int(i) for i in mask[mask].index[:limit].tolist()]


def check_numeric_range_rules(df: pd.DataFrame, rules: dict[str, Any]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for variable, config in rules.get("numeric_ranges", {}).items():
        if variable not in df.columns:
            continue
        values = pd.to_numeric(df[variable], errors="coerce")
        mask = pd.Series(False, index=df.index)
        if config.get("min") is not None:
            mask |= values < config["min"]
        if config.get("max") is not None:
            mask |= values > config["max"]
        mask &= values.notna()
        if mask.any():
            warnings.append(
                make_warning(
                    f"MED_RANGE_{variable.upper()}",
                    "medical_plausibility",
                    str(config.get("severity", "high")),
                    variable,
                    str(config.get("description", f"{variable} is outside the configured plausibility range.")),
                    str(config.get("recommended_action", f"Verify {variable} values.")),
                    count=int(mask.sum()),
                    example_rows=_example_rows(mask),
                    human_confirmation_required=True,
                )
            )
    return warnings


def _logic_rule_lookup(rules: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {rule.get("name"): rule for rule in rules.get("logic_rules", [])}


def check_cross_field_rules(df: pd.DataFrame, rules: dict[str, Any]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    logic = _logic_rule_lookup(rules)

    if {"sbp", "dbp"}.issubset(df.columns):
        sbp = pd.to_numeric(df["sbp"], errors="coerce")
        dbp = pd.to_numeric(df["dbp"], errors="coerce")
        mask = sbp.notna() & dbp.notna() & (sbp < dbp)
        if mask.any():
            rule = logic.get("sbp_less_than_dbp", {})
            warnings.append(
                make_warning(
                    str(rule.get("id", "MED_LOGIC_SBP_DBP")),
                    "medical_plausibility",
                    str(rule.get("severity", "critical")),
                    "sbp, dbp",
                    str(rule.get("description", "Systolic blood pressure is lower than diastolic blood pressure.")),
                    str(rule.get("recommended_action", "Verify blood pressure entries.")),
                    count=int(mask.sum()),
                    example_rows=_example_rows(mask),
                    human_confirmation_required=True,
                )
            )

    if {"visit_date", "death_date"}.issubset(df.columns):
        visit = pd.to_datetime(df["visit_date"], errors="coerce")
        death = pd.to_datetime(df["death_date"], errors="coerce")
        mask = visit.notna() & death.notna() & (death < visit)
        if mask.any():
            rule = logic.get("death_before_visit", {})
            warnings.append(
                make_warning(
                    str(rule.get("id", "MED_LOGIC_DEATH_VISIT")),
                    "medical_plausibility",
                    str(rule.get("severity", "critical")),
                    "death_date, visit_date",
                    str(rule.get("description", "Death date is earlier than visit date.")),
                    str(rule.get("recommended_action", "Verify visit and death dates.")),
                    count=int(mask.sum()),
                    example_rows=_example_rows(mask),
                    human_confirmation_required=True,
                )
            )

    if "follow_up_days" in df.columns:
        follow_up = pd.to_numeric(df["follow_up_days"], errors="coerce")
        mask = follow_up.notna() & (follow_up < 0)
        if mask.any():
            rule = logic.get("negative_follow_up", {})
            warnings.append(
                make_warning(
                    str(rule.get("id", "MED_LOGIC_NEGATIVE_FOLLOW_UP")),
                    "medical_plausibility",
                    str(rule.get("severity", "critical")),
                    "follow_up_days",
                    str(rule.get("description", "Follow-up time is negative.")),
                    str(rule.get("recommended_action", "Verify follow-up duration.")),
                    count=int(mask.sum()),
                    example_rows=_example_rows(mask),
                    human_confirmation_required=True,
                )
            )
    return warnings


def check_duplicate_patient_id(df: pd.DataFrame) -> list[dict[str, Any]]:
    if "patient_id" not in df.columns:
        return []
    mask = df["patient_id"].duplicated(keep=False) & df["patient_id"].notna()
    if not mask.any():
        return []
    return [
        make_warning(
            "MED_DUPLICATE_PATIENT_ID",
            "data_quality",
            "critical",
            "patient_id",
            "Duplicate patient_id values were detected.",
            "Confirm whether repeated IDs are duplicate records or longitudinal visits.",
            count=int(mask.sum()),
            example_rows=_example_rows(mask),
            human_confirmation_required=True,
        )
    ]


def _normalize_sex(value: str) -> str:
    value = str(value).strip().lower()
    if value in {"male", "m", "1"}:
        return "male"
    if value in {"female", "f", "0"}:
        return "female"
    return "unknown"


def check_coding_inconsistency(df: pd.DataFrame) -> list[dict[str, Any]]:
    if "sex" not in df.columns:
        return []
    raw_values = {str(value).strip() for value in df["sex"].dropna().unique()}
    normalized = {_normalize_sex(value) for value in raw_values}
    normalized.discard("unknown")
    if len(raw_values) > len(normalized) and len(normalized) <= 2:
        return [
            make_warning(
                "MED_SEX_CODING_INCONSISTENCY",
                "data_quality",
                "medium",
                "sex",
                "Sex coding uses multiple representations that appear to map to the same concepts.",
                "Standardize coding after confirming the intended values.",
                count=len(raw_values),
                example_rows=[],
                human_confirmation_required=True,
            )
        ]
    return []


def check_medical_rules(
    df: pd.DataFrame,
    rules_path: str | Path | None = None,
    rules: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    loaded_rules = _load_yaml(rules_path, rules)
    warnings: list[dict[str, Any]] = []
    warnings.extend(check_numeric_range_rules(df, loaded_rules))
    warnings.extend(check_cross_field_rules(df, loaded_rules))
    warnings.extend(check_unit_warnings(df))
    warnings.extend(check_duplicate_patient_id(df))
    warnings.extend(check_coding_inconsistency(df))
    return warnings
