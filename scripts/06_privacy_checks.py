from __future__ import annotations

from typing import Any

import pandas as pd


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
}

DATE_IDENTIFIER_TERMS = {
    "birth_date",
    "date_of_birth",
    "dob",
}


def _normalize(column: str) -> str:
    return column.strip().lower().replace(" ", "_").replace("-", "_")


def _warning(issue_id: str, severity: str, variable: str, description: str, action: str) -> dict[str, Any]:
    return {
        "issue_id": issue_id,
        "issue_type": "privacy_risk",
        "severity": severity,
        "variable": variable,
        "count": None,
        "example_rows": [],
        "description": description,
        "recommended_action": action,
        "human_confirmation_required": True,
    }


def check_privacy_risks(df: pd.DataFrame) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for column in df.columns:
        normalized = _normalize(column)
        if normalized in DIRECT_IDENTIFIER_TERMS or any(term in normalized for term in DIRECT_IDENTIFIER_TERMS):
            warnings.append(
                _warning(
                    "PRIV_DIRECT_IDENTIFIER",
                    "critical",
                    column,
                    "Potential direct identifier field detected.",
                    "Do not upload identifiable patient data to external AI tools. Remove, hash, or replace this field before analysis.",
                )
            )
        elif normalized in DATE_IDENTIFIER_TERMS:
            warnings.append(
                _warning(
                    "PRIV_DATE_IDENTIFIER",
                    "high",
                    column,
                    "Potential date-related identifier field detected.",
                    "Confirm whether the date is needed and whether it should be generalized before sharing.",
                )
            )
    return warnings
