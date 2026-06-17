from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any


FLAGGED_RECORDS_SCHEMA_VERSION = "0.2.0"

FLAGGED_RECORD_FIELDS = [
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

_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d{1,3}[-.\s()]*)?(?:\d[-.\s()]*){7,}\d(?!\w)")
_LONG_NUMERIC_ID_RE = re.compile(r"(?<!\w)\d{9,}(?!\w)")
_API_KEY_RE = re.compile(
    r"(?<!\w)(?:sk-[A-Za-z0-9_-]{12,}|[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{6,})(?!\w)"
)


def sanitize_flagged_record_text(value: object) -> str:
    """Redact direct identifiers if unexpected warning text contains them."""
    if value is None:
        return ""
    text = str(value)
    text = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    text = _API_KEY_RE.sub("[REDACTED_SECRET]", text)
    text = _LONG_NUMERIC_ID_RE.sub("[REDACTED_ID]", text)
    text = _PHONE_RE.sub("[REDACTED_PHONE]", text)
    return text


def normalize_bool(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return "true" if value.strip().lower() in {"1", "true", "yes", "y"} else "false"
    return "true" if bool(value) else "false"


def build_flagged_records(warnings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for warning in warnings:
        example_rows = warning.get("example_rows") or []
        if not isinstance(example_rows, list):
            continue

        for row_index in example_rows:
            records.append(
                {
                    "schema_version": FLAGGED_RECORDS_SCHEMA_VERSION,
                    "issue_id": sanitize_flagged_record_text(warning.get("issue_id")),
                    "issue_type": sanitize_flagged_record_text(warning.get("issue_type")),
                    "severity": sanitize_flagged_record_text(warning.get("severity")),
                    "variable": sanitize_flagged_record_text(warning.get("variable")),
                    "row_index": row_index,
                    "source_warning_count": "" if warning.get("count") is None else warning.get("count"),
                    "safe_evidence_summary": sanitize_flagged_record_text(warning.get("description")),
                    "recommended_action": sanitize_flagged_record_text(warning.get("recommended_action")),
                    "human_confirmation_required": normalize_bool(warning.get("human_confirmation_required")),
                }
            )
    return records


def validate_flagged_record_schema(record: dict[str, Any]) -> bool:
    if set(record.keys()) != set(FLAGGED_RECORD_FIELDS):
        return False
    if record.get("schema_version") != FLAGGED_RECORDS_SCHEMA_VERSION:
        return False
    if record.get("row_index") in (None, ""):
        return False
    if record.get("human_confirmation_required") not in {"true", "false"}:
        return False
    return all(field in record for field in FLAGGED_RECORD_FIELDS)


def save_flagged_records(records: list[dict[str, Any]], output_path: str | Path) -> None:
    if not all(validate_flagged_record_schema(record) for record in records):
        raise ValueError("Flagged records do not match the expected v0.2 schema.")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FLAGGED_RECORD_FIELDS)
        writer.writeheader()
        writer.writerows(records)
