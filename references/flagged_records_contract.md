# Flagged Records CSV Contract

Use this file when editing `core/flagged_records.py`, `core/orchestrator.py`, or CLI support for flagged record output.

## Purpose

`flagged_records.csv` is a privacy-safe row-reference issue index. It records which existing warning flagged which row reference. It is not a raw data export, data cleaning output, or clinical review packet.

The output is optional. No CSV should be written unless the user provides `--flagged-records-output` or `flagged_records_output_path`.

The schema is unchanged after WS5, WS6, and WS7. Missingness warnings and unit
warnings can flow into `flagged_records.csv` only when they are existing
`AuditWarning` dictionaries with `example_rows`. Iterative extraction requests
do not enter `flagged_records.csv`.

## Required Header

The CSV header order is fixed:

```csv
schema_version,issue_id,issue_type,severity,variable,row_index,source_warning_count,safe_evidence_summary,recommended_action,human_confirmation_required
```

## Row Rules

- Build rows only from existing `AuditWarning` dictionaries.
- Create one CSV row per `warning.example_rows` entry.
- Create no CSV row for warnings with empty `example_rows`.
- Create rows for missingness or unit warnings only through the same `example_rows` rule.
- Create no rows from iterative extraction requests.
- Copy `example_rows` values exactly into `row_index`.
- Do not renumber rows.
- Do not look up raw dataframe row content.
- Do not include raw cell values, full rows, patient names, phone numbers, emails, addresses, medical record numbers, clinical free text, secrets, or external LLM output.

## Allowed Evidence

Each row may contain only:

- schema version
- issue ID
- issue type
- severity
- variable name
- row reference
- warning count
- sanitized warning description
- sanitized recommended action
- human confirmation flag

## Privacy Safety

`safe_evidence_summary` and `recommended_action` must come from warning metadata. They must be passed through a conservative sanitizer that redacts obvious direct identifiers if unexpected text includes them.

The stronger privacy rule is structural: `flagged_records.csv` must never receive raw dataframe values.
