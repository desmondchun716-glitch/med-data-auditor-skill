from __future__ import annotations

from typing import Any

import pandas as pd

from .schemas import make_warning


DIRECT_IDENTIFIER_TERMS = {
    "name",
    "patient_name",
    "phone",
    "mobile",
    "email",
    "address",
    "id_card",
    "identity",
    "social_security_number",
    "ssn",
    "medical_record_number",
    "mrn",
    "姓名",
    "手机号",
    "电话",
    "身份证",
    "身份证号",
    "住址",
    "地址",
    "病案号",
}

DATE_IDENTIFIER_TERMS = {
    "birth_date",
    "date_of_birth",
    "dob",
    "出生日期",
}


def _normalize(column: str) -> str:
    return column.strip().lower().replace(" ", "_").replace("-", "_")


def _is_direct_identifier_name(column: str) -> bool:
    normalized = _normalize(column)
    return normalized in DIRECT_IDENTIFIER_TERMS or any(term in normalized for term in DIRECT_IDENTIFIER_TERMS)


def _is_date_identifier_name(column: str) -> bool:
    normalized = _normalize(column)
    return normalized in DATE_IDENTIFIER_TERMS or "date" in normalized


def detect_potential_pii_columns(df: pd.DataFrame) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for column in df.columns:
        normalized = _normalize(column)
        if _is_direct_identifier_name(column):
            warnings.append(
                make_warning(
                    "PRIV_DIRECT_IDENTIFIER",
                    "privacy_risk",
                    "critical",
                    column,
                    "Potential direct identifier field detected.",
                    "Do not upload identifiable patient data to external AI tools. Remove, hash, or replace this field before analysis.",
                    human_confirmation_required=True,
                )
            )
        elif normalized in DATE_IDENTIFIER_TERMS:
            warnings.append(
                make_warning(
                    "PRIV_DATE_IDENTIFIER",
                    "privacy_risk",
                    "high",
                    column,
                    "Potential date-related identifier field detected.",
                    "Confirm whether the date is needed and whether it should be generalized before sharing.",
                    human_confirmation_required=True,
                )
            )
    return warnings


def check_small_cell_risk(df: pd.DataFrame, categorical_columns: list[str] | None = None, min_count: int = 5) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    columns = categorical_columns or [column for column in df.columns if not pd.api.types.is_numeric_dtype(df[column])]
    for column in columns:
        if column not in df.columns:
            continue
        if _is_direct_identifier_name(column) or _is_date_identifier_name(column):
            continue
        counts = df[column].dropna().astype(str).value_counts()
        if len(counts) <= 1:
            continue
        unique_rate = len(counts) / max(int(counts.sum()), 1)
        if unique_rate >= 0.95:
            continue
        rare_levels = counts[counts < min_count]
        if not rare_levels.empty:
            warnings.append(
                make_warning(
                    f"PRIV_SMALL_CELL_{column.upper()}",
                    "privacy_risk",
                    "medium",
                    column,
                    f"Variable `{column}` has {len(rare_levels)} rare categories with fewer than {min_count} records.",
                    "Avoid exposing detailed subgroup summaries that could increase re-identification risk.",
                    count=int(len(rare_levels)),
                    human_confirmation_required=True,
                )
            )
    return warnings


def generate_privacy_warnings(df: pd.DataFrame) -> list[dict[str, Any]]:
    warnings = detect_potential_pii_columns(df)
    warnings.extend(check_small_cell_risk(df))
    return warnings


def check_privacy_risks(df: pd.DataFrame) -> list[dict[str, Any]]:
    return generate_privacy_warnings(df)
