# Med Data Auditor Skill Specification

## Intent

Med Data Auditor Skill turns a biomedical or public health CSV plus a user research question into a compact, evidence-based audit report. The tool performs local full-data scanning and deterministic checks so an AI assistant can interpret structured evidence instead of sampling raw rows.

The project is one main skill named `med-data-auditor-skill`. Future categories are internal modules or roadmap items, not separate skills. The first version is a portfolio-ready v0.1: small, runnable, safe, and clear about limitations.

## Scope

In scope:

- CSV input
- Python, pandas, PyYAML, and Markdown output
- Dataset profiling
- Missingness and duplicate patient ID checks
- Configurable medical plausibility rules
- Statistical analysis-readiness checks
- Potential identifier field detection
- Question-driven exposure, outcome, confounder mapping, and basic study design warnings
- Synthetic sample data, sample report, and simple tests

Out of scope:

- Web UI
- External LLM API calls
- Real patient data
- Automatic full data cleaning
- Automatic paper writing
- Complex causal inference
- Production clinical data management
- Regulatory-grade CDISC SDTM or ADaM support
- Separate child skills for future categories
- GitHub publishing before the user confirms the local version is ready

## v0.2 Contract

v0.2 must strengthen the existing single-skill workflow without changing the project identity.

All v0.2 work must satisfy:

1. The project remains one main Agent Skill named `med-data-auditor-skill`.
2. Future capabilities are internal workstreams, modules, scripts, rules, or references.
3. No child skills, extra `SKILL.md`, or separate skill directories are allowed.
4. The v0.1 core pipeline remains stable unless a workstream explicitly requires a minimal change.
5. Each branch has one active v0.2 workstream.
6. Any new output contract preserves privacy safety, deterministic validation, and human confirmation requirements.

The seven v0.2 internal workstreams are:

1. Single-skill guardrails and v0.2 contract
2. Audit log contract
3. Flagged records contract
4. Unit warning contract
5. Missingness and analysis-readiness metrics
6. Iterative extraction protocol
7. Report contract and token metrics polish

### WS2 Audit Log Contract

WS2 adds an optional `audit_log.json` output. The audit log is a privacy-safe machine-readable audit trail for reproducibility and downstream tooling.

It may include run metadata, safe file metadata, rule fingerprints, dataset shape, variable roles, study design summary, warning counts, warning objects, token metrics, and output paths.

It must not include raw rows, raw cell values, direct identifier values, secrets, full raw datasets, or external LLM outputs as authoritative evidence.

### WS3 Flagged Records Contract

WS3 adds an optional `flagged_records.csv` output. The flagged records CSV is a privacy-safe row-reference issue index for human confirmation and downstream tooling.

It may include schema version, issue ID, issue type, severity, variable, row reference, source warning count, sanitized warning description, sanitized recommended action, and human confirmation flag.

It must be generated only when explicitly requested. It must not include raw rows, raw cell values, direct identifier values, clinical free text, corrected values, automatic cleaning actions, secrets, or external LLM output.

Warnings with `example_rows` produce one CSV row per example row. Warnings without `example_rows` stay in the Markdown report and optional audit log only.

### WS4 Unit Warning Contract

WS4 adds deterministic warning-only checks for possible biomedical unit or scale mismatches.

Unit warnings use the existing `AuditWarning` schema with `issue_type="medical_plausibility"`, `UNIT_`-prefixed issue IDs, cautious descriptions, affected-row counts, example row indexes, and required human confirmation.

The initial checks cover explicitly labeled blood pressure, temperature, percent/fraction, height, weight, glucose, creatinine, and lipid fields. They use conservative majority-pattern heuristics and do not infer a unit for generic unlabeled laboratory variables.

WS4 must not convert units, mutate source data, create cleaned output, repeat raw values in warning text, add a new issue type, make clinical claims, or implement later v0.2 workstreams.

### WS5 Missingness And Analysis-Readiness Contract

WS5 adds deterministic, privacy-safe missingness evidence to the existing profiler and statistical warning pipeline.

It includes dataset-level missingness metrics, row-level burden, role-aware complete-case readiness for exposure/outcome/confounders, near-empty columns, top co-occurring missingness pairs, and transparent readiness flags.

WS5 metrics are stored inside the existing profile and `audit_log.json` dataset summary. WS5 warnings use the existing `AuditWarning` schema and existing `data_quality` or `statistical_risk` issue types.

WS5 must not impute, mutate the source DataFrame, drop rows or columns, create cleaned output, fit models, classify MCAR/MAR/MNAR, analyze sensitive subgroup missingness, or implement WS6/WS7.

### WS6 Iterative Extraction Protocol

WS6 adds deterministic, privacy-safe next-step requests generated from variable-role gaps, study-design uncertainty, unit warnings, missingness evidence, privacy warnings, outcome coding needs, repeated patient IDs, population ambiguity, and time-window evidence.

Each request includes a deterministic ID, priority, request type, trigger source, related variables and issue IDs, a concise question, analysis-readiness rationale, expected response type, safe-response guidance, and required human confirmation.

Requests are deduplicated, limited to 10 by default, rendered in the Markdown report, and stored under `audit_log.json` `analysis_context.extraction_requests`.

WS6 must not request raw patient rows or direct identifier values, call external services, automate data extraction, mutate the source dataset, add a new CLI flag, add a new output file, add a new audit-log top-level key, change the flagged-record schema, clean or impute data, convert units, fit models, or implement WS7.

The detailed runtime contract is in `references/iterative_extraction_protocol.md`.

### WS7 Report And Token Metrics Contract

WS7 finalizes the existing Markdown report and token metrics as the last v0.2
workstream.

The report keeps a stable 13-section order from `User Question` through
`Limitations and Safety Notes`. It remains compact, deterministic,
evidence-based, and free of raw row samples or raw cell values.

Token metrics remain under the existing audit-log `token_metrics` key. They
record the character-based estimation method, source and report character
counts, approximate token counts, compression ratio, warning count, report
section count, and an explicit caveat that the values are not exact tokenizer
output. The older `original_csv_estimated_tokens` field remains available as a
backward-compatible alias.

WS7 must not add new audit domains, warning types, CLI flags, output files,
audit-log top-level keys, tokenizer dependencies, external API calls, cleaning,
imputation, unit conversion, statistical modeling, or v0.3 behavior.

The detailed runtime contract is in `references/report_contract.md`.

## Users And Trigger Context

- Primary users: biomedical, public health, clinical research, RWE, CRO, MCM/ICM, and health survey learners or analysts.
- Common requests: "audit this medical dataset", "check if this CSV is ready for analysis", "summarize data quality before AI analysis", "is this dataset ready to study BMI and hypertension".
- Should not trigger for: non-health generic data cleaning unless the user explicitly asks for biomedical-style analysis-readiness auditing.

## Runtime Contract

- Required first actions: verify privacy safety, run the local orchestrator when a CSV is available, read the Markdown report before advising.
- Required outputs: report with dataset overview, relevant variables and study design, missingness, biomedical warnings, statistical warnings, privacy / PII warnings, analysis-readiness notes, iterative extraction requests, human confirmation questions, token-saving summary, and limitations.
- Non-negotiable constraints: never overwrite source data, never treat warnings as clinical truth, never upload identifiable patient data.
- Expected bundled files loaded at runtime: `SKILL.md`; optional routed files in `references/` only when modifying reports, rules, or scope.

## Source And Evidence Model

Authoritative sources:

- `med_data_auditor_skill_spec.md`
- local Agent Skills authoring rules used during creation
- generated sample data and pytest results

Useful improvement sources:

- positive examples: reports that identify injected issues and give cautious analysis guidance
- negative examples: reports that overclaim, miss privacy warnings, or turn into generic cleaning
- validation results: CLI run output, sample report, pytest, and skill validator output

Data that must not be stored:

- secrets
- real patient records
- direct identifiers from user datasets
- private source data not needed for reproducible debugging

## Reference Architecture

- `SKILL.md` contains runtime activation, workflow, script contract, safety boundaries, and validation commands.
- `references/` contains report contracts, iterative extraction guidance, rule authoring guidance, and roadmap scope control for one main skill.
- `core/` contains the internal business modules plus `schemas.py` and `orchestrator.py`.
- `scripts/` contains synthetic data generation and compatibility wrappers.
- `rules/` contains YAML medical, statistical, and variable dictionary configuration.
- `tests/` contains lightweight regression checks for the first version.

## Validation

- Lightweight validation: run sample data generation, full audit CLI, pytest, and skill structural validator.
- Deeper validation: run against additional synthetic health survey, RWE, and clinical trial-like CSVs.
- Holdout examples: future versions should keep small de-identified or synthetic edge-case fixtures.
- Acceptance gates: one-command audit works, injected issues are detected, report includes all required sections, and safety limitations are visible.

## v0.2 Validation Gates

Documentation-only v0.2 work must pass:

```bash
git diff --name-only
git ls-files --cached --others --exclude-standard -- '*SKILL.md'
```

Expected result for the second command: only the root `SKILL.md` exists.

Documentation-only workstreams should also confirm no core implementation files changed:

```bash
git diff -- core rules scripts tests data reports examples run_audit.py requirements.txt
```

Expected result: no diff.

Code-changing v0.2 work must additionally pass:

```bash
python scripts/generate_sample_data.py
python run_audit.py --data data/sample_medical_data.csv --question "Is BMI associated with hypertension after adjusting for age and sex?" --output reports/sample_audit_report.md
python run_audit.py --data data/sample_medical_data.csv --question "Is BMI associated with hypertension after adjusting for age and sex?" --output reports/sample_audit_report.md --audit-log-output reports/sample_audit_log.json --flagged-records-output reports/sample_flagged_records.csv
python -m pytest
```

The PR must explain if any command is not run.

## Known Limitations

- Variable role mapping uses keyword matching, not advanced NLP.
- Medical plausibility rules are generic and require human confirmation.
- Statistical risk checks are readiness warnings, not formal modeling.
- v0.2 token estimates are transparent character-based engineering estimates, not exact tokenizer counts.

## Maintenance Notes

- Update `SKILL.md` when runtime workflow, trigger language, safety rules, or validation commands change.
- Update `SOURCES.md` when decisions, gaps, source material, or validation evidence change.
- Update `references/` when optional report, rule, or roadmap guidance becomes too detailed for `SKILL.md`.
