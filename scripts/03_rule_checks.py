from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml


DEFAULT_RULES = Path(__file__).resolve().parents[1] / "rules" / "medical_rules.yaml"


def _load_yaml(path: str | Path | None, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    if fallback is not None:
        return fallback
    with Path(path or DEFAULT_RULES).open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _example_rows(mask: pd.Series, limit: int = 5) -> list[int]:
    return [int(i) for i in mask[mask].index[:limit].tolist()]


def _warning(
    issue_id: str,
    issue_type: str,
    severity: str,
    variable: str,
    count: int | None,
    example_rows: list[int],
    description: str,
    recommended_action: str,
    human_confirmation_required: bool = True,
) -> dict[str, Any]:
    return {
        "issue_id": issue_id,
        "issue_type": issue_type,
        "severity": severity,
        "variable": variable,
        "count": count,
        "example_rows": example_rows,
        "description": description,
        "recommended_action": recommended_action,
        "human_confirmation_required": human_confirmation_required,
    }


def _logic_rule_lookup(rules: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {rule.get("name"): rule for rule in rules.get("logic_rules", [])}


def check_medical_rules(
    df: pd.DataFrame,
    rules_path: str | Path | None = None,
    rules: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    loaded_rules = _load_yaml(rules_path, rules)
    warnings: list[dict[str, Any]] = []

    for variable, config in loaded_rules.get("numeric_ranges", {}).items():
        if variable not in df.columns:
            continue
        values = pd.to_numeric(df[variable], errors="coerce")
        lower = config.get("min")
        upper = config.get("max")
        mask = pd.Series(False, index=df.index)
        if lower is not None:
            mask |= values < lower
        if upper is not None:
            mask |= values > upper
        mask &= values.notna()
        if mask.any():
            warnings.append(
                _warning(
                    issue_id=f"MED_RANGE_{variable.upper()}",
                    issue_type="medical_plausibility",
                    severity=str(config.get("severity", "high")),
                    variable=variable,
                    count=int(mask.sum()),
                    example_rows=_example_rows(mask),
                    description=str(config.get("description", f"{variable} is outside the configured plausibility range.")),
                    recommended_action=str(config.get("recommended_action", f"Verify {variable} values.")),
                )
            )

    logic = _logic_rule_lookup(loaded_rules)

    if {"sbp", "dbp"}.issubset(df.columns):
        sbp = pd.to_numeric(df["sbp"], errors="coerce")
        dbp = pd.to_numeric(df["dbp"], errors="coerce")
        mask = sbp.notna() & dbp.notna() & (sbp < dbp)
        if mask.any():
            rule = logic.get("sbp_less_than_dbp", {})
            warnings.append(
                _warning(
                    issue_id=str(rule.get("id", "MED_LOGIC_SBP_DBP")),
                    issue_type="medical_plausibility",
                    severity=str(rule.get("severity", "critical")),
                    variable="sbp, dbp",
                    count=int(mask.sum()),
                    example_rows=_example_rows(mask),
                    description=str(rule.get("description", "Systolic blood pressure is lower than diastolic blood pressure.")),
                    recommended_action=str(rule.get("recommended_action", "Verify blood pressure entries.")),
                )
            )

    if {"visit_date", "death_date"}.issubset(df.columns):
        visit = pd.to_datetime(df["visit_date"], errors="coerce")
        death = pd.to_datetime(df["death_date"], errors="coerce")
        mask = visit.notna() & death.notna() & (death < visit)
        if mask.any():
            rule = logic.get("death_before_visit", {})
            warnings.append(
                _warning(
                    issue_id=str(rule.get("id", "MED_LOGIC_DEATH_VISIT")),
                    issue_type="medical_plausibility",
                    severity=str(rule.get("severity", "critical")),
                    variable="death_date, visit_date",
                    count=int(mask.sum()),
                    example_rows=_example_rows(mask),
                    description=str(rule.get("description", "Death date is earlier than visit date.")),
                    recommended_action=str(rule.get("recommended_action", "Verify visit and death dates.")),
                )
            )

    if "follow_up_days" in df.columns:
        follow_up = pd.to_numeric(df["follow_up_days"], errors="coerce")
        mask = follow_up.notna() & (follow_up < 0)
        if mask.any():
            rule = logic.get("negative_follow_up", {})
            warnings.append(
                _warning(
                    issue_id=str(rule.get("id", "MED_LOGIC_NEGATIVE_FOLLOW_UP")),
                    issue_type="medical_plausibility",
                    severity=str(rule.get("severity", "critical")),
                    variable="follow_up_days",
                    count=int(mask.sum()),
                    example_rows=_example_rows(mask),
                    description=str(rule.get("description", "Follow-up time is negative.")),
                    recommended_action=str(rule.get("recommended_action", "Verify follow-up duration.")),
                )
            )

    if "patient_id" in df.columns:
        mask = df["patient_id"].duplicated(keep=False) & df["patient_id"].notna()
        if mask.any():
            warnings.append(
                _warning(
                    issue_id="MED_DUPLICATE_PATIENT_ID",
                    issue_type="data_quality",
                    severity="critical",
                    variable="patient_id",
                    count=int(mask.sum()),
                    example_rows=_example_rows(mask),
                    description="Duplicate patient_id values were detected.",
                    recommended_action="Confirm whether repeated IDs are duplicate records or longitudinal visits.",
                    human_confirmation_required=True,
                )
            )

    if "sex" in df.columns:
        raw_values = {str(value).strip() for value in df["sex"].dropna().unique()}
        normalized = {_normalize_sex(value) for value in raw_values}
        normalized.discard("unknown")
        if len(raw_values) > len(normalized) and len(normalized) <= 2:
            warnings.append(
                _warning(
                    issue_id="MED_SEX_CODING_INCONSISTENCY",
                    issue_type="data_quality",
                    severity="medium",
                    variable="sex",
                    count=len(raw_values),
                    example_rows=[],
                    description="Sex coding uses multiple representations that appear to map to the same concepts.",
                    recommended_action="Standardize coding after confirming the intended values.",
                    human_confirmation_required=True,
                )
            )

    return warnings


def _normalize_sex(value: str) -> str:
    value = str(value).strip().lower()
    if value in {"male", "m", "1"}:
        return "male"
    if value in {"female", "f", "0"}:
        return "female"
    return "unknown"
