# v0.2 Report Contract

Use this reference when editing `core/report_generator.py`, token metrics, or
tests that validate the generated Markdown report.

## Purpose

The report compresses deterministic, full-dataset audit evidence into a
human-readable analysis-readiness summary. It is not a clinical report, a
cleaned dataset, a model result, or a raw-data extract.

## Required Section Order

The v0.2 report contains exactly these numbered sections in this order:

1. User Question
2. Executive Summary
3. Dataset Overview
4. Relevant Variables and Study Design
5. Missing Data Summary
6. Biomedical Plausibility Warnings
7. Statistical Risk Warnings
8. Privacy / PII Warnings
9. Analysis-readiness Notes
10. Iterative Extraction Requests
11. Questions for Human Confirmation
12. Token-saving Summary
13. Limitations and Safety Notes

The document title is:

```text
# AI-ready Biomedical Data Audit Report
```

## Required Content

The report must include:

- the user question and an explicit readiness verdict
- warning counts and compact priority findings
- dataset row and column counts plus potential ID columns
- variable roles and inferred study design
- missing-value counts and missingness-readiness metrics
- biomedical, statistical, and privacy warnings
- analysis-readiness guidance without fitted model output
- iterative extraction requests and human confirmation questions
- approximate token metrics with their estimation caveat
- explicit limitations and safety statements

## Compactness Limits

- Priority findings: top 6
- Missing columns: top 15
- Co-occurring missingness pairs: top 5
- Iterative extraction requests: top 10
- Human confirmation questions: top 10

## Evidence And Privacy Boundary

Allowed report evidence:

- counts and rates
- variable names
- issue IDs and severity
- recommended actions
- safe row indexes
- schema-safe extraction requests
- approximate token estimates

Forbidden report content:

- raw row samples or full records
- raw cell values
- patient names, phone numbers, emails, addresses, or ID values
- clinical free text
- secrets
- corrected or imputed values

## Token Metrics Contract

Token metrics remain under the existing `audit_log.json` top-level
`token_metrics` key. The v0.2 shape includes:

```text
estimation_method
source_csv_character_count
source_csv_estimated_tokens
original_csv_estimated_tokens
audit_report_character_count
audit_report_estimated_tokens
compression_ratio
warning_count
report_section_count
notes
```

`original_csv_estimated_tokens` is retained as a backward-compatible alias for
`source_csv_estimated_tokens`.

The estimation method is `approx_chars_div_4`. These values are approximate
character-based engineering estimates for compression tracking and audit
traceability, not exact tokenizer counts.

## Required Safety Language

The report must clearly state that this workflow:

- is not a clinical decision tool
- does not diagnose disease or recommend treatment
- does not fit statistical models
- does not clean or modify source data
- does not replace a statistician or clinical data manager
- should not be used with identifiable patient data
- must not send identifiable patient data to external AI systems

## Validation

Regression tests must verify:

- required sections are present and ordered
- generated report text contains no stale v0.1 release wording
- compactness limits remain enforced
- missingness and iterative extraction sections remain present
- token estimates disclose their approximate method and caveat
- raw synthetic values do not appear in the report
- audit-log top-level keys remain unchanged
- token metric fields and types validate

## Non-goals

WS7 does not add new audit domains, warning types, CLI flags, output files,
external tokenizer dependencies, external API calls, cleaning, imputation,
unit conversion, statistical modeling, or v0.3 behavior.
