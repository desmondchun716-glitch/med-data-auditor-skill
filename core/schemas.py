from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


VALID_SEVERITIES = {"critical", "high", "medium", "low", "info"}
VALID_ISSUE_TYPES = {
    "data_quality",
    "medical_plausibility",
    "statistical_risk",
    "study_design",
    "privacy_risk",
    "variable_mapping",
    "token_compression",
}

REQUIRED_WARNING_FIELDS = {
    "issue_id",
    "issue_type",
    "severity",
    "variable",
    "count",
    "example_rows",
    "description",
    "recommended_action",
    "human_confirmation_required",
}


@dataclass
class AuditWarning:
    issue_id: str
    issue_type: str
    severity: str
    variable: str | None
    count: int | None
    example_rows: list[int] = field(default_factory=list)
    description: str = ""
    recommended_action: str = ""
    human_confirmation_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        severity = self.severity if self.severity in VALID_SEVERITIES else "medium"
        issue_type = self.issue_type if self.issue_type in VALID_ISSUE_TYPES else "data_quality"
        payload = asdict(self)
        payload["severity"] = severity
        payload["issue_type"] = issue_type
        return payload


def make_warning(
    issue_id: str,
    issue_type: str,
    severity: str,
    variable: str | None,
    description: str,
    recommended_action: str,
    count: int | None = None,
    example_rows: list[int] | None = None,
    human_confirmation_required: bool = True,
) -> dict[str, Any]:
    return AuditWarning(
        issue_id=issue_id,
        issue_type=issue_type,
        severity=severity,
        variable=variable,
        count=count,
        example_rows=example_rows or [],
        description=description,
        recommended_action=recommended_action,
        human_confirmation_required=human_confirmation_required,
    ).to_dict()


def validate_warning_schema(warning: dict[str, Any]) -> bool:
    if set(warning.keys()) != REQUIRED_WARNING_FIELDS:
        return False
    if warning["severity"] not in VALID_SEVERITIES:
        return False
    if warning["issue_type"] not in VALID_ISSUE_TYPES:
        return False
    if not isinstance(warning["issue_id"], str) or not warning["issue_id"]:
        return False
    if warning["variable"] is not None and not isinstance(warning["variable"], str):
        return False
    if warning["count"] is not None and not isinstance(warning["count"], int):
        return False
    if not isinstance(warning["example_rows"], list):
        return False
    if not isinstance(warning["description"], str) or not warning["description"]:
        return False
    if not isinstance(warning["recommended_action"], str) or not warning["recommended_action"]:
        return False
    return isinstance(warning["human_confirmation_required"], bool)
