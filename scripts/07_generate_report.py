from __future__ import annotations

from pathlib import Path
from typing import Any


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _list_or_none(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "None identified"


def _warning_table(warnings: list[dict[str, Any]]) -> str:
    if not warnings:
        return "No warnings detected.\n"

    sorted_warnings = sorted(warnings, key=lambda item: (SEVERITY_ORDER.get(str(item.get("severity")), 9), str(item.get("issue_id"))))
    lines = [
        "| Severity | Issue | Variable | Count | Description | Recommended Action | Example Rows |",
        "|---|---|---|---:|---|---|---|",
    ]
    for warning in sorted_warnings:
        examples = ", ".join(str(row) for row in warning.get("example_rows", []) or [])
        lines.append(
            "| {severity} | {issue} | {variable} | {count} | {description} | {action} | {examples} |".format(
                severity=_escape(warning.get("severity", "")),
                issue=_escape(warning.get("issue_id", "")),
                variable=_escape(warning.get("variable", "")),
                count="" if warning.get("count") is None else _escape(warning.get("count")),
                description=_escape(warning.get("description", "")),
                action=_escape(warning.get("recommended_action", "")),
                examples=_escape(examples),
            )
        )
    return "\n".join(lines) + "\n"


def _missing_summary(profile: dict[str, Any], key_vars: list[str]) -> str:
    missing = profile.get("missing_summary", {})
    rows = []
    for variable, summary in missing.items():
        count = summary.get("missing_count", 0)
        rate = summary.get("missing_rate", 0)
        if count:
            role = "key variable" if variable in key_vars else ""
            rows.append((rate, variable, count, role))
    if not rows:
        return "No missing values detected.\n"
    rows.sort(reverse=True)
    lines = ["| Variable | Missing Count | Missing Rate | Role |", "|---|---:|---:|---|"]
    for rate, variable, count, role in rows[:15]:
        lines.append(f"| `{variable}` | {count} | {rate:.1%} | {role} |")
    return "\n".join(lines) + "\n"


def _recommended_plan(profile: dict[str, Any], relevant_vars: dict[str, Any], warnings: list[dict[str, Any]]) -> str:
    exposure = relevant_vars.get("exposure", [])
    outcome = relevant_vars.get("outcome", [])
    confounders = relevant_vars.get("confounders", [])
    critical_or_high = [w for w in warnings if w.get("severity") in {"critical", "high"}]

    if not exposure or not outcome:
        return (
            "The research question does not clearly map to both an exposure and an outcome. "
            "Ask the user to confirm variable roles before recommending a statistical analysis."
        )

    outcome_name = outcome[0]
    categorical = profile.get("categorical_summary", {}).get(outcome_name, {})
    variable_types = profile.get("variable_types", {})

    if len(categorical) == 2:
        analysis_direction = "A binary-outcome association analysis may be considered after readiness issues are reviewed"
    elif variable_types.get(outcome_name) == "numeric":
        analysis_direction = "A numeric-outcome association analysis may be considered after readiness issues are reviewed"
    else:
        analysis_direction = "A descriptive or group-comparison analysis may be considered after confirming the outcome type"

    plan = (
        f"{analysis_direction}. The primary exposure is {_list_or_none(exposure)}, the outcome is {_list_or_none(outcome)}, "
        f"and the requested adjustment variables are {_list_or_none(confounders)}. "
    )
    if critical_or_high:
        top = "; ".join(f"{w.get('issue_id')} on {w.get('variable')}" for w in critical_or_high[:5])
        plan += f"Do not proceed to modeling until these high-priority issues are reviewed: {top}. "
    plan += "v0.1 does not fit statistical models or report model estimates. Interpret future results as association unless the study design and analysis plan justify causal language."
    return plan


def _confirmation_questions(relevant_vars: dict[str, Any], warnings: list[dict[str, Any]]) -> list[str]:
    questions: list[str] = []
    if not relevant_vars.get("exposure"):
        questions.append("Which variable is the primary exposure or predictor?")
    if not relevant_vars.get("outcome"):
        questions.append("Which variable is the outcome?")
    if relevant_vars.get("unavailable_variables"):
        questions.append("The question mentions variables not found in the dataset: " + ", ".join(relevant_vars["unavailable_variables"]) + ". Are the column names different?")

    for warning in warnings:
        if warning.get("human_confirmation_required") and warning.get("severity") in {"critical", "high"}:
            questions.append(f"Please confirm `{warning.get('issue_id')}` for `{warning.get('variable')}`: {warning.get('description')}")
    return questions[:10]


def _estimate_tokens_from_file(path: str | Path | None, fallback_chars: int) -> int:
    if path is None:
        return max(1, fallback_chars // 4)
    try:
        text = Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return max(1, fallback_chars // 4)
    return max(1, len(text) // 4)


def generate_markdown_report(
    question: str,
    profile: dict[str, Any],
    relevant_vars: dict[str, Any],
    medical_warnings: list[dict[str, Any]],
    statistical_warnings: list[dict[str, Any]],
    privacy_warnings: list[dict[str, Any]],
    data_path: str | Path | None = None,
) -> str:
    key_vars = []
    for role in ("exposure", "outcome", "confounders"):
        key_vars.extend(relevant_vars.get(role, []) or [])

    all_warnings = medical_warnings + statistical_warnings + privacy_warnings
    duplicates = profile.get("duplicates", {})
    variable_types = profile.get("variable_types", {})
    type_counts = {}
    for var_type in variable_types.values():
        type_counts[var_type] = type_counts.get(var_type, 0) + 1
    type_text = ", ".join(f"{count} {var_type}" for var_type, count in sorted(type_counts.items()))

    questions = _confirmation_questions(relevant_vars, all_warnings)
    question_lines = "\n".join(f"- {item}" for item in questions) if questions else "- No immediate confirmation questions beyond routine review."

    major_issues = [w for w in all_warnings if w.get("severity") in {"critical", "high"}]
    major_issue_text = "; ".join(f"{w.get('issue_id')} ({w.get('variable')})" for w in major_issues[:8]) or "no critical or high-severity warnings"

    body = f"""# AI-ready Biomedical Data Audit Report

## 1. User Question

{question}

## 2. Dataset Overview

- Rows: {profile.get("n_rows")}
- Columns: {profile.get("n_columns")}
- Variable type summary: {type_text or "not available"}
- Duplicate rows: {duplicates.get("duplicate_rows", 0)}
- Duplicate patient ID rows: {duplicates.get("duplicate_patient_id", 0)}

## 3. Relevant Variables

- Exposure: {_list_or_none(relevant_vars.get("exposure", []))}
- Outcome: {_list_or_none(relevant_vars.get("outcome", []))}
- Confounders: {_list_or_none(relevant_vars.get("confounders", []))}
- Suggested additional confounders: {_list_or_none(relevant_vars.get("suggested_confounders", []))}
- Unavailable variables from question: {_list_or_none(relevant_vars.get("unavailable_variables", []))}

## 4. Missing Data Summary

{_missing_summary(profile, key_vars)}

## 5. Medical Plausibility Warnings

These warnings indicate potential plausibility issues. They do not prove that records are incorrect and require human confirmation.

{_warning_table(medical_warnings)}

## 6. Statistical Risk Warnings

{_warning_table(statistical_warnings)}

## 7. Privacy / Identifier Warnings

Do not upload identifiable patient data to external AI tools.

{_warning_table(privacy_warnings)}

## 8. Analysis-readiness Notes

{_recommended_plan(profile, relevant_vars, all_warnings)}

## 9. Questions for Human Confirmation

{question_lines}

## 10. Token-saving Summary

The dataset contains {profile.get("n_rows")} records and {profile.get("n_columns")} variables. The user question maps to exposure {_list_or_none(relevant_vars.get("exposure", []))}, outcome {_list_or_none(relevant_vars.get("outcome", []))}, and confounders {_list_or_none(relevant_vars.get("confounders", []))}. Major issues include {major_issue_text}. This report is designed to let an AI assistant reason from compact full-dataset evidence rather than raw row samples.

## 11. Limitations

- This report is not a clinical decision tool.
- This report does not verify real-world medical truth.
- This workflow does not replace a statistician or clinical data manager.
- This workflow should not be used with identifiable patient data.
- Medical plausibility warnings require human confirmation.
- v0.1 supports analysis-readiness review, not automatic causal inference.
"""

    raw_tokens = _estimate_tokens_from_file(data_path, int(profile.get("n_rows", 0)) * int(profile.get("n_columns", 0)) * 24)
    report_tokens = max(1, len(body) // 4)
    ratio = raw_tokens / report_tokens if report_tokens else 0
    token_note = f"\nApproximate source CSV tokens: {raw_tokens}. Approximate report tokens: {report_tokens}. Compression ratio: {ratio:.1f}:1.\n"
    return body + token_note
