# Audit Log Contract

## Purpose

`audit_log.json` is an optional machine-readable audit trail for reproducibility and downstream tooling.

Audit log records audit evidence, not patient data.

The Markdown report remains the primary human-facing output. The audit log captures the deterministic evidence needed to understand a run: metadata, rule fingerprints, dataset shape, variable-role mapping, study-design summary, warning counts, warning objects, token metrics, and output paths.

## Non-goals

The audit log is not:

- a copy of the raw dataset
- a data-cleaning output
- a flagged-records export
- a statistical model result
- a clinical decision record
- an external LLM transcript
- a regulatory-grade clinical data management artifact

## Privacy Rule

Do not store raw patient-level data in `audit_log.json`.

Allowed evidence must be compact and non-identifying. Column names may appear because the audit workflow depends on variable names, but direct values from sensitive columns must not appear.

## Top-level Schema

The v0.2 audit log uses this top-level shape:

```json
{
  "schema_version": "0.2.0",
  "tool": {},
  "run": {},
  "inputs": {},
  "outputs": {},
  "dataset_summary": {},
  "analysis_context": {},
  "warnings": {},
  "token_metrics": {},
  "privacy_safety": {}
}
```

## Allowed Fields

The audit log may include:

- schema version
- tool name and target version
- run ID and UTC timestamp
- user research question
- safe file metadata: file name, extension, size, and short SHA-256 fingerprint
- rule paths and short SHA-256 fingerprints
- report and audit log output paths
- dataset row count, column count, column names, variable types, missingness summary, and potential ID-like column names
- variable-role mapping
- study-design summary
- warning counts by category
- warning objects that follow the shared `AuditWarning` schema
- token compression metrics
- privacy-safety flags

## Forbidden Fields

The audit log must never include:

- raw dataset rows
- raw cell values
- direct identifier values
- patient names
- phone numbers
- email values
- addresses
- medical record numbers
- ID card numbers
- free-text clinical notes
- secrets or API keys
- full raw CSV content
- external LLM outputs as authoritative evidence

## Relationship To AuditWarning

Warning items must use the existing shared `AuditWarning` schema from `core/schemas.py`.

The audit log must not introduce a second warning model. Future warning categories should extend the shared warning schema and then appear in the audit log through the same warning list.

## CLI Behavior

The existing command remains unchanged:

```bash
python run_audit.py --data data/sample_medical_data.csv --question "Is BMI associated with hypertension after adjusting for age and sex?" --output reports/sample_audit_report.md
```

Generate the audit log only when explicitly requested:

```bash
python run_audit.py --data data/sample_medical_data.csv --question "Is BMI associated with hypertension after adjusting for age and sex?" --output reports/sample_audit_report.md --audit-log-output reports/sample_audit_log.json
```

## Validation Rules

Validation must confirm:

- `schema_version` is `0.2.0`
- required top-level keys are present
- warning items follow the shared `AuditWarning` schema
- privacy-safety flags are present and false for raw rows, raw cell values, direct identifier values, and external LLM output
- generated logs do not contain direct PII values from synthetic privacy tests

## Example audit_log.json Shape

```json
{
  "schema_version": "0.2.0",
  "tool": {
    "name": "med-data-auditor-skill",
    "version_target": "v0.2"
  },
  "run": {
    "run_id": "uuid4-string",
    "created_at_utc": "2026-06-17T00:00:00Z",
    "user_question": "Is BMI associated with hypertension?"
  },
  "inputs": {
    "data_file": {
      "file_name": "sample_medical_data.csv",
      "file_extension": ".csv",
      "file_size_bytes": 12345,
      "sha256_12": "abc123def456"
    },
    "rules": {
      "medical_rules": {
        "path": "rules/medical_rules.yaml",
        "sha256_12": "abc123def456"
      }
    }
  },
  "outputs": {
    "report_path": "reports/sample_audit_report.md",
    "audit_log_path": "reports/sample_audit_log.json"
  },
  "dataset_summary": {
    "row_count": 300,
    "column_count": 17,
    "columns": ["age", "sex", "bmi"]
  },
  "analysis_context": {
    "variable_roles": {},
    "study_design": {}
  },
  "warnings": {
    "counts": {},
    "items": []
  },
  "token_metrics": {},
  "privacy_safety": {
    "raw_rows_stored": false,
    "raw_cell_values_stored": false,
    "direct_identifier_values_stored": false,
    "external_llm_output_stored": false,
    "human_confirmation_required": true
  }
}
```

## Future Extensions

Future workstreams may build on the audit log by adding:

- WS3 flagged-records references
- WS5 expanded analysis-readiness metrics
- WS6 deterministic iterative extraction request metadata
- stronger rule-version provenance

Future extensions must preserve the privacy rule and must not turn the audit log into a raw-data export.
