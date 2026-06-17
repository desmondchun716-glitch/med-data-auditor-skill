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
