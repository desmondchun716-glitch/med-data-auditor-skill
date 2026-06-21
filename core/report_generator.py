from __future__ import annotations

from pathlib import Path
from typing import Any


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def _escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _list_or_none(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "None identified"


def _warning_counts(warnings: list[dict[str, Any]]) -> dict[str, int]:
    counts = {severity: 0 for severity in SEVERITY_ORDER}
    for warning in warnings:
        severity = str(warning.get("severity", "medium"))
        counts[severity] = counts.get(severity, 0) + 1
    return counts


def _readiness_verdict(warnings: list[dict[str, Any]]) -> str:
    counts = _warning_counts(warnings)
    if counts.get("critical", 0) or counts.get("high", 0):
        return "Not ready for modeling: review critical and high-priority audit findings first."
    if counts.get("medium", 0):
        return "Conditionally ready for exploratory review after medium-priority findings are checked."
    return "No major readiness blockers detected by v0.1 checks."


def _render_warning_summary(warnings: list[dict[str, Any]]) -> str:
    counts = _warning_counts(warnings)
    return (
        "| Critical | High | Medium | Low | Info |\n"
        "|---:|---:|---:|---:|---:|\n"
        f"| {counts.get('critical', 0)} | {counts.get('high', 0)} | {counts.get('medium', 0)} | {counts.get('low', 0)} | {counts.get('info', 0)} |\n"
    )


def _render_priority_findings(warnings: list[dict[str, Any]], limit: int = 6) -> str:
    priority = sorted(
        [warning for warning in warnings if warning.get("severity") in {"critical", "high"}],
        key=lambda item: (SEVERITY_ORDER.get(str(item.get("severity")), 9), str(item.get("issue_id"))),
    )
    if not priority:
        return "- No critical or high-priority findings detected by v0.1 checks.\n"
    lines = []
    for warning in priority[:limit]:
        count = warning.get("count")
        row_word = "row" if count == 1 else "rows"
        count_text = f" ({count} affected {row_word})" if count is not None else ""
        lines.append(f"- `{warning.get('issue_id')}` on `{warning.get('variable')}`{count_text}: {warning.get('description')}")
    return "\n".join(lines) + "\n"


def render_warning_section(warnings: list[dict[str, Any]], title: str | None = None) -> str:
    if not warnings:
        return "No warnings detected by v0.1 checks.\n"
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


def render_dataset_overview(profile: dict[str, Any]) -> str:
    duplicates = profile.get("duplicates", {})
    variable_types = profile.get("variable_types", {})
    type_counts = {}
    for var_type in variable_types.values():
        type_counts[var_type] = type_counts.get(var_type, 0) + 1
    type_text = ", ".join(f"{count} {var_type}" for var_type, count in sorted(type_counts.items()))
    return f"""- Rows: {profile.get("n_rows")}
- Columns: {profile.get("n_columns")}
- Variable type summary: {type_text or "not available"}
- Potential ID columns: {_list_or_none(profile.get("potential_id_columns", []))}
- Duplicate rows: {duplicates.get("duplicate_rows", 0)}
- Duplicate patient ID rows: {duplicates.get("duplicate_patient_id", 0)}
"""


def render_variable_roles(variable_roles: dict[str, Any], study_design: dict[str, Any] | None = None) -> str:
    design = study_design or {}
    return f"""- Exposure: {_list_or_none(variable_roles.get("exposure", []))}
- Outcome: {_list_or_none(variable_roles.get("outcome", []))}
- Confounders: {_list_or_none(variable_roles.get("confounders", []))}
- Suggested additional confounders: {_list_or_none(variable_roles.get("suggested_confounders", []))}
- Unavailable variables from question: {_list_or_none(variable_roles.get("unavailable_variables", []))}
- Inferred study design: `{design.get("inferred_design", "not assessed")}`
- Study design confidence: `{design.get("confidence", "not assessed")}`
- Study design note: {design.get("note", "Ask the user to confirm study design.")}
"""


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


def _missingness_readiness_summary(profile: dict[str, Any]) -> str:
    metrics = profile.get("missingness_readiness") or {}
    if not metrics:
        return "Missingness readiness metrics are not available.\n"

    key_variables = metrics.get("key_variables") or []
    key_rate = metrics.get("complete_case_rate_for_key_variables")
    key_text = (
        f"{key_rate:.1%} across {_list_or_none(key_variables)}"
        if key_rate is not None
        else "not assessed because no exposure, outcome, or confounder variables were mapped"
    )
    pairs = metrics.get("top_missingness_cooccurrence_pairs") or []
    if pairs:
        pair_lines = "\n".join(
            (
                f"- `{pair['variable_a']}` + `{pair['variable_b']}`: "
                f"{pair['joint_missing_count']} rows ({pair['joint_missing_rate']:.1%})"
            )
            for pair in pairs[:5]
        )
    else:
        pair_lines = "- No co-occurring missingness pairs detected."

    flags = metrics.get("readiness_flags") or []
    flag_text = ", ".join(f"`{flag}`" for flag in flags) if flags else "none detected"
    return f"""### Key-variable complete-case readiness

- Complete-case rate for mapped key variables: {key_text}
- Rows missing any mapped key variable: {metrics.get("rows_missing_any_key_variable") if key_rate is not None else "not assessed"}

### Row-level missingness burden

- Rows with any missing value: {metrics.get("rows_with_any_missing", 0)} ({metrics.get("rows_with_any_missing_rate", 0):.1%})
- Rows missing at least {metrics.get("high_row_missing_fraction", 0.30):.0%} of columns: {metrics.get("rows_with_high_missing_burden", 0)} ({metrics.get("rows_with_high_missing_burden_rate", 0):.1%})
- Overall missing-cell rate: {metrics.get("overall_missing_cell_rate", 0):.1%}

### Missingness co-occurrence screening

{pair_lines}

### Missingness mechanism screening caveat

{metrics.get("mechanism_screening_caveat", "This screening is evidence triage and requires human review.")}

- Readiness flags: {flag_text}
"""


def generate_recommended_analysis_plan(
    variable_roles: dict[str, Any],
    statistical_warnings: list[dict[str, Any]],
    medical_warnings: list[dict[str, Any]],
    profile: dict[str, Any] | None = None,
) -> str:
    profile = profile or {}
    exposure = variable_roles.get("exposure", [])
    outcome = variable_roles.get("outcome", [])
    confounders = variable_roles.get("confounders", [])
    high_priority = [w for w in medical_warnings + statistical_warnings if w.get("severity") in {"critical", "high"}]

    if not exposure or not outcome:
        return (
            "The research question does not clearly map to both an exposure and an outcome. "
            "Ask the user to confirm variable roles before recommending a statistical analysis direction."
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
    if high_priority:
        top = "; ".join(f"{w.get('issue_id')} on {w.get('variable')}" for w in high_priority[:5])
        plan += f"Do not proceed to modeling until these high-priority issues are reviewed: {top}. "
    plan += "v0.1 does not fit statistical models or report model estimates. Interpret future results as association unless the study design and analysis plan justify causal language."
    return plan


def _confirmation_questions(variable_roles: dict[str, Any], warnings: list[dict[str, Any]]) -> list[str]:
    questions: list[str] = []
    if not variable_roles.get("exposure"):
        questions.append("Which variable is the primary exposure or predictor?")
    if not variable_roles.get("outcome"):
        questions.append("Which variable is the outcome?")
    if variable_roles.get("unavailable_variables"):
        questions.append("The question mentions variables not found in the dataset: " + ", ".join(variable_roles["unavailable_variables"]) + ". Are the column names different?")
    for warning in warnings:
        if warning.get("human_confirmation_required") and warning.get("severity") in {"critical", "high"}:
            questions.append(f"Please confirm `{warning.get('issue_id')}` for `{warning.get('variable')}`: {warning.get('description')}")
    return questions[:10]


def render_extraction_requests(extraction_requests: list[dict[str, Any]]) -> str:
    caveat = (
        "These requests ask for metadata, column names, definitions, coding rules, units, and "
        "de-identification confirmation. Do not provide raw patient rows or direct identifier values."
    )
    if not extraction_requests:
        return f"{caveat}\n\nNo structured iterative extraction requests were generated beyond routine review.\n"

    lines = [
        caveat,
        "",
        "| Priority | Request Type | Related Variables | Request | Safe Response |",
        "|---|---|---|---|---|",
    ]
    for request in extraction_requests[:10]:
        related_variables = ", ".join(
            f"`{variable}`" for variable in request.get("related_variables", [])
        ) or "None"
        lines.append(
            "| {priority} | {request_type} | {related_variables} | {question} | {safe_response} |".format(
                priority=_escape(request.get("priority", "")),
                request_type=_escape(request.get("request_type", "")),
                related_variables=_escape(related_variables),
                question=_escape(request.get("question", "")),
                safe_response=_escape(request.get("safe_response_guidance", "")),
            )
        )
    return "\n".join(lines) + "\n"


def estimate_token_compression(data_path: str | Path | None, report_text: str) -> dict[str, Any]:
    raw_tokens = 1
    if data_path is not None:
        try:
            text = Path(data_path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = Path(data_path).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            text = ""
        raw_tokens = max(1, len(text) // 4)
    report_tokens = max(1, len(report_text) // 4)
    return {
        "original_csv_estimated_tokens": raw_tokens,
        "audit_report_estimated_tokens": report_tokens,
        "compression_ratio": round(raw_tokens / report_tokens, 1),
    }


def generate_markdown_report(
    question: str,
    profile: dict[str, Any],
    variable_roles: dict[str, Any] | None = None,
    relevant_vars: dict[str, Any] | None = None,
    medical_warnings: list[dict[str, Any]] | None = None,
    statistical_warnings: list[dict[str, Any]] | None = None,
    privacy_warnings: list[dict[str, Any]] | None = None,
    study_design: dict[str, Any] | None = None,
    study_design_warnings: list[dict[str, Any]] | None = None,
    extraction_requests: list[dict[str, Any]] | None = None,
    token_metrics: dict[str, Any] | None = None,
    data_path: str | Path | None = None,
) -> str:
    variable_roles = variable_roles or relevant_vars or {}
    medical_warnings = medical_warnings or []
    statistical_warnings = statistical_warnings or []
    privacy_warnings = privacy_warnings or []
    study_design_warnings = study_design_warnings or []
    extraction_requests = extraction_requests or []

    key_vars: list[str] = []
    for role in ("exposure", "outcome", "confounders"):
        key_vars.extend(variable_roles.get(role, []) or [])

    all_warnings = medical_warnings + statistical_warnings + privacy_warnings + study_design_warnings
    questions = _confirmation_questions(variable_roles, all_warnings)
    question_lines = "\n".join(f"- {item}" for item in questions) if questions else "- No immediate confirmation questions beyond routine review."
    major_issues = [w for w in all_warnings if w.get("severity") in {"critical", "high"}]
    major_issue_text = "; ".join(f"{w.get('issue_id')} ({w.get('variable')})" for w in major_issues[:8]) or "no critical or high-severity warnings"

    body = f"""# AI-ready Biomedical Data Audit Report

## 1. User Question

{question}

## 2. Executive Summary

**Readiness verdict:** {_readiness_verdict(all_warnings)}

This v0.1 audit scanned the full CSV locally and generated a compact evidence report for biomedical analysis-readiness review. It did not clean the data, fit statistical models, call external LLM APIs, or make clinical decisions.

**Warning summary**

{_render_warning_summary(all_warnings)}
**Priority findings**

{_render_priority_findings(all_warnings)}
## 3. Dataset Overview

{render_dataset_overview(profile)}
## 4. Relevant Variables and Study Design

{render_variable_roles(variable_roles, study_design)}
{render_warning_section(study_design_warnings)}

## 5. Missing Data Summary

{_missing_summary(profile, key_vars)}
{_missingness_readiness_summary(profile)}

## 6. Biomedical Plausibility Warnings

These warnings indicate potential plausibility issues. They do not prove that records are incorrect and require human confirmation.

{render_warning_section(medical_warnings)}

## 7. Statistical Risk Warnings

{render_warning_section(statistical_warnings)}

## 8. Privacy / PII Warnings

Do not upload identifiable patient data to external AI tools. Treat privacy warnings as blockers for external sharing until the data is de-identified or the field is removed, hashed, generalized, or otherwise handled according to the study policy.

{render_warning_section(privacy_warnings)}

## 9. Analysis-readiness Notes

{generate_recommended_analysis_plan(variable_roles, statistical_warnings + study_design_warnings, medical_warnings, profile)}

## 10. Iterative Extraction Requests

{render_extraction_requests(extraction_requests)}
## 11. Questions for Human Confirmation

{question_lines}

## 12. Token-saving Summary

The dataset contains {profile.get("n_rows")} records and {profile.get("n_columns")} variables. The user question maps to exposure {_list_or_none(variable_roles.get("exposure", []))}, outcome {_list_or_none(variable_roles.get("outcome", []))}, and confounders {_list_or_none(variable_roles.get("confounders", []))}. Major issues include {major_issue_text}. This report is designed to let an AI assistant reason from compact full-dataset evidence rather than raw row samples.

## 13. Limitations and Safety Notes

- This report is not a clinical decision tool.
- This report does not diagnose disease or recommend treatment.
- This report does not verify real-world medical truth.
- This workflow does not replace a statistician or clinical data manager.
- This workflow should not be used with identifiable patient data.
- Do not upload real patient data or direct identifiers to external AI systems.
- Medical plausibility warnings require human confirmation.
- Privacy warnings require review before external sharing.
- v0.1 supports analysis-readiness review, not automatic causal inference.
"""

    metrics = token_metrics or estimate_token_compression(data_path, body)
    token_note = (
        "\nApproximate source CSV tokens: {raw}. Approximate report tokens: {report}. "
        "Compression ratio: {ratio}:1.\n"
    ).format(
        raw=metrics.get("original_csv_estimated_tokens"),
        report=metrics.get("audit_report_estimated_tokens"),
        ratio=metrics.get("compression_ratio"),
    )
    return body + token_note


def save_report(report_text: str, output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report_text, encoding="utf-8")
