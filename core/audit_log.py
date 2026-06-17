from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import uuid
from typing import Any

from .schemas import validate_warning_schema


AUDIT_LOG_SCHEMA_VERSION = "0.2.0"


def short_sha256(path: str | Path) -> str | None:
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return None

    digest = hashlib.sha256()
    with file_path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:12]


def safe_file_metadata(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    metadata: dict[str, Any] = {
        "file_name": file_path.name,
        "file_extension": file_path.suffix.lower(),
        "file_size_bytes": None,
        "sha256_12": short_sha256(file_path),
    }
    if file_path.exists() and file_path.is_file():
        metadata["file_size_bytes"] = int(file_path.stat().st_size)
    return metadata


def _safe_rule_metadata(rule_paths: dict[str, str | Path]) -> dict[str, dict[str, Any]]:
    return {
        name: {
            "path": str(path),
            "sha256_12": short_sha256(path),
        }
        for name, path in rule_paths.items()
    }


def _safe_dataset_summary(profile: dict[str, Any]) -> dict[str, Any]:
    missing_summary = profile.get("missing_summary") or {}
    return {
        "row_count": profile.get("n_rows"),
        "column_count": profile.get("n_columns"),
        "columns": list(profile.get("columns") or []),
        "variable_types": dict(profile.get("variable_types") or {}),
        "missing_summary": missing_summary,
        "potential_id_columns": list(profile.get("potential_id_columns") or []),
    }


def _warning_counts(
    *,
    intake_warnings: list[dict[str, Any]],
    study_design_warnings: list[dict[str, Any]],
    medical_warnings: list[dict[str, Any]],
    statistical_warnings: list[dict[str, Any]],
    privacy_warnings: list[dict[str, Any]],
) -> dict[str, int]:
    return {
        "intake": len(intake_warnings),
        "study_design": len(study_design_warnings),
        "medical": len(medical_warnings),
        "statistical": len(statistical_warnings),
        "privacy": len(privacy_warnings),
    }


def _warning_counts_by_field(warnings: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for warning in warnings:
        value = warning.get(field) or "unspecified"
        counts[str(value)] = counts.get(str(value), 0) + 1
    return dict(sorted(counts.items()))


def _warning_items(
    *,
    intake_warnings: list[dict[str, Any]],
    study_design_warnings: list[dict[str, Any]],
    medical_warnings: list[dict[str, Any]],
    statistical_warnings: list[dict[str, Any]],
    privacy_warnings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        *intake_warnings,
        *study_design_warnings,
        *medical_warnings,
        *statistical_warnings,
        *privacy_warnings,
    ]


def _deterministic_run_id(
    *,
    data_file_metadata: dict[str, Any],
    question: str,
    output_path: str | Path,
    audit_log_output_path: str | Path | None,
    rule_metadata: dict[str, dict[str, Any]],
) -> str:
    seed = json.dumps(
        {
            "schema_version": AUDIT_LOG_SCHEMA_VERSION,
            "data_file": data_file_metadata,
            "question": question,
            "report_path": str(output_path),
            "audit_log_path": str(audit_log_output_path) if audit_log_output_path else None,
            "rules": rule_metadata,
        },
        sort_keys=True,
        default=str,
    )
    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))


def build_audit_log(
    *,
    data_path: str | Path,
    question: str,
    output_path: str | Path,
    audit_log_output_path: str | Path | None,
    metadata: dict[str, Any],
    profile: dict[str, Any],
    variable_roles: dict[str, Any],
    study_design: dict[str, Any],
    intake_warnings: list[dict[str, Any]],
    study_design_warnings: list[dict[str, Any]],
    medical_warnings: list[dict[str, Any]],
    statistical_warnings: list[dict[str, Any]],
    privacy_warnings: list[dict[str, Any]],
    token_metrics: dict[str, Any],
    rule_paths: dict[str, str | Path],
) -> dict[str, Any]:
    counts = _warning_counts(
        intake_warnings=intake_warnings,
        study_design_warnings=study_design_warnings,
        medical_warnings=medical_warnings,
        statistical_warnings=statistical_warnings,
        privacy_warnings=privacy_warnings,
    )
    warnings = _warning_items(
        intake_warnings=intake_warnings,
        study_design_warnings=study_design_warnings,
        medical_warnings=medical_warnings,
        statistical_warnings=statistical_warnings,
        privacy_warnings=privacy_warnings,
    )

    data_file_metadata = safe_file_metadata(data_path)
    data_file_metadata["column_count_from_intake"] = metadata.get("n_columns")
    rule_metadata = _safe_rule_metadata(rule_paths)
    total_warning_count = len(warnings)
    counts_by_severity = _warning_counts_by_field(warnings, "severity")
    counts_by_issue_type = _warning_counts_by_field(warnings, "issue_type")

    return {
        "schema_version": AUDIT_LOG_SCHEMA_VERSION,
        "tool": {
            "name": "med-data-auditor-skill",
            "version_target": "v0.2",
        },
        "run": {
            "run_id": _deterministic_run_id(
                data_file_metadata=data_file_metadata,
                question=question,
                output_path=output_path,
                audit_log_output_path=audit_log_output_path,
                rule_metadata=rule_metadata,
            ),
            "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "user_question": question,
        },
        "inputs": {
            "data_file": data_file_metadata,
            "rules": rule_metadata,
        },
        "outputs": {
            "report_path": str(output_path),
            "audit_log_path": str(audit_log_output_path) if audit_log_output_path else None,
        },
        "dataset_summary": _safe_dataset_summary(profile),
        "analysis_context": {
            "variable_roles": variable_roles,
            "study_design": study_design,
        },
        "warnings": {
            "counts": counts,
            "counts_by_category": counts,
            "counts_by_severity": counts_by_severity,
            "counts_by_issue_type": counts_by_issue_type,
            "total_count": total_warning_count,
            "items": warnings,
        },
        "token_metrics": token_metrics,
        "privacy_safety": {
            "raw_rows_stored": False,
            "raw_cell_values_stored": False,
            "direct_identifier_values_stored": False,
            "external_llm_output_stored": False,
            "human_confirmation_required": True,
        },
    }


def validate_audit_log_schema(audit_log: dict[str, Any]) -> bool:
    required_top_level = {
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
    if set(audit_log.keys()) != required_top_level:
        return False
    if audit_log.get("schema_version") != AUDIT_LOG_SCHEMA_VERSION:
        return False
    warnings = audit_log.get("warnings")
    if not isinstance(warnings, dict):
        return False
    required_warning_keys = {
        "counts",
        "counts_by_category",
        "counts_by_severity",
        "counts_by_issue_type",
        "total_count",
        "items",
    }
    if set(warnings.keys()) != required_warning_keys:
        return False
    counts = warnings.get("counts")
    counts_by_category = warnings.get("counts_by_category")
    counts_by_severity = warnings.get("counts_by_severity")
    counts_by_issue_type = warnings.get("counts_by_issue_type")
    total_count = warnings.get("total_count")
    items = warnings.get("items")
    if not isinstance(counts, dict) or not all(isinstance(value, int) for value in counts.values()):
        return False
    if counts_by_category != counts:
        return False
    for grouped_counts in (counts_by_severity, counts_by_issue_type):
        if not isinstance(grouped_counts, dict) or not all(isinstance(value, int) for value in grouped_counts.values()):
            return False
    if not isinstance(items, list):
        return False
    if not isinstance(total_count, int) or total_count != len(items):
        return False
    if sum(counts_by_severity.values()) != total_count or sum(counts_by_issue_type.values()) != total_count:
        return False
    if not all(isinstance(item, dict) and validate_warning_schema(item) for item in items):
        return False
    privacy = audit_log.get("privacy_safety")
    if not isinstance(privacy, dict):
        return False
    return (
        privacy.get("raw_rows_stored") is False
        and privacy.get("raw_cell_values_stored") is False
        and privacy.get("direct_identifier_values_stored") is False
        and privacy.get("external_llm_output_stored") is False
        and privacy.get("human_confirmation_required") is True
    )


def save_audit_log(audit_log: dict[str, Any], output_path: str | Path) -> None:
    if not validate_audit_log_schema(audit_log):
        raise ValueError("Audit log does not match the expected v0.2 schema.")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(audit_log, ensure_ascii=False, indent=2), encoding="utf-8")
