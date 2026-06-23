# Med Data Auditor Skill

Token-efficient biomedical data analysis-readiness auditing for CSV datasets.

This is not a generic data cleaning script. It is an audit-first workflow that scans biomedical and public health datasets locally, detects analysis-readiness risks, and produces a compact AI-ready Markdown report before any modeling or interpretation.

## Overview

Med Data Auditor Skill profiles biomedical and public health datasets locally, detects data quality issues, biomedical plausibility problems, statistical analysis risks, and privacy concerns, then generates compact AI-ready Markdown reports for iterative analysis.

## Core Promise

The original v0.1 promise was narrow and concrete:

```text
CSV + biomedical research question -> AI-ready analysis-readiness audit report
```

The current v0.2.0 release keeps the same audit-first identity while adding
privacy-safe structured outputs, unit warnings, missingness-readiness metrics,
iterative extraction requests, and a stable report/token contract.

## Why This Project Matters

Large biomedical datasets are costly and unreliable for an AI assistant to inspect directly. This tool scans the full dataset locally, detects data quality and analysis-readiness risks, and generates a compact Markdown report that an AI assistant or human reviewer can use as evidence.

The current release is intentionally focused: CSV input, pandas profiling, YAML rules, deterministic checks, privacy-safe structured outputs, and an AI-ready report. It does not clean the original data, make clinical decisions, or run production-grade clinical data management.

This repository contains one main skill named `med-data-auditor-skill`. Future directions should become internal modules or roadmap items after the core workflow is strong enough, not separate skills.

## Core Idea

Programmatic scanning first, AI interpretation second. The program scans the full dataset locally; the AI reads only the compressed evidence report; the human confirms warnings before analysis decisions.

## What This Project Does Not Do

- No automatic data cleaning
- No fitted statistical models
- No odds ratios, p-values, or confidence intervals
- No visualization or web UI
- No external LLM API calls
- No LLM Council or multi-agent runtime layer
- No real patient data support
- No clinical decision-making

## Features

- CSV dataset profiling
- Missingness and duplicate patient ID detection
- Configurable medical plausibility checks
- Warning-only checks for possible biomedical unit or scale mismatches
- Statistical analysis-readiness warnings
- Privacy-safe missingness pattern and key-variable complete-case readiness metrics
- Potential identifier and privacy field detection
- Question-driven exposure, outcome, and confounder mapping
- AI-ready Markdown audit report
- Optional privacy-safe machine-readable audit log JSON
- Optional privacy-safe flagged records CSV for row-level warning references
- Deterministic privacy-safe iterative extraction requests for metadata and human confirmation
- Stable v0.2 report contract with 13 ordered sections and explicit safety boundaries
- Transparent approximate token metrics for compression tracking and audit traceability
- Synthetic sample data with injected quality issues
- Pytest coverage for core checks, output contracts, report sections, token metrics, and privacy-safe schemas

## What It Checks

- Data intake and file metadata
- Data profiling and type detection
- Biomedical plausibility warnings
- Possible unit mismatches for explicitly labeled blood pressure, temperature, percent/fraction, height, weight, glucose, creatinine, and lipid fields
- Statistical analysis-readiness risks
- Row-level missingness burden, near-empty columns, key-variable complete cases, and co-occurring missingness patterns
- Variable role mapping and basic study design warnings
- Privacy / PII fields and small-cell risk
- Safe next-step requests for variable roles, units, coding, missingness, study design, privacy, repeated measures, population, and time windows
- Token compression estimate

## Quick Start

```bash
pip install -r requirements.txt

python scripts/generate_sample_data.py

python run_audit.py \
  --data data/sample_medical_data.csv \
  --question "Is BMI associated with hypertension after adjusting for age and sex?" \
  --output reports/sample_audit_report.md
```

Open `reports/sample_audit_report.md` to review the generated audit.

The command prints a short run summary and writes the full report to Markdown.

Full v0.2 output:

```bash
python run_audit.py \
  --data data/sample_medical_data.csv \
  --question "Is BMI associated with hypertension after adjusting for age and sex?" \
  --output reports/sample_audit_report.md \
  --audit-log-output reports/sample_audit_log.json \
  --flagged-records-output reports/sample_flagged_records.csv
```

Optional audit log output:

```bash
python run_audit.py \
  --data data/sample_medical_data.csv \
  --question "Is BMI associated with hypertension after adjusting for age and sex?" \
  --output reports/sample_audit_report.md \
  --audit-log-output reports/sample_audit_log.json
```

The audit log is designed for reproducibility and downstream tooling. It records audit evidence and warning summaries, not raw patient data.

Optional flagged records output:

```bash
python run_audit.py \
  --data data/sample_medical_data.csv \
  --question "Is BMI associated with hypertension after adjusting for age and sex?" \
  --output reports/sample_audit_report.md \
  --audit-log-output reports/sample_audit_log.json \
  --flagged-records-output reports/sample_flagged_records.csv
```

The flagged records CSV records safe issue evidence and row references from existing warnings. It does not store raw patient rows or raw cell values.

The report also includes a compact `Iterative Extraction Requests` section. These requests ask for metadata, column names, definitions, coding rules, units, or de-identification confirmation. They do not request raw patient rows and are also stored under `audit_log.json` `analysis_context` when the audit log is enabled.

The v0.2 Markdown report follows the stable 13-section contract documented in
`references/report_contract.md`. Token metrics use a local character-count / 4
engineering estimate and explicitly do not claim exact tokenizer accuracy.

Example CLI output:

```text
Wrote audit report to reports/sample_audit_report.md
Wrote audit log to reports/sample_audit_log.json
Wrote flagged records to reports/sample_flagged_records.csv
Warnings: intake=0, medical=7, statistical=9, privacy=2, study_design=0
Approximate token compression: 9236 -> 3302 (2.8:1)
```

Exact counts may change as deterministic rules and synthetic fixtures evolve.

## Example Use Case

User question:

```text
Is BMI associated with hypertension after adjusting for age and sex?
```

The auditor checks whether the dataset is ready for that analysis by reviewing key variables, BMI missingness, hypertension outcome balance, duplicate patient IDs, medical plausibility warnings, privacy-sensitive fields, and limitations such as association versus causation.

## Example Output

See `reports/sample_audit_report.md`.

Core synthetic issue coverage:

| Issue family | Example |
|---|---|
| Medical plausibility | Age, BMI, blood pressure, date, and follow-up issues |
| Data quality | Duplicate patient IDs |
| Unit warnings | Possible unit or scale mismatch checks |
| Statistical readiness | Outcome balance, key variables, sample size, and missingness |
| Missingness readiness | Complete-case rate, row burden, and co-occurrence |
| Privacy | PII-like fields and small-cell risk |
| Iterative extraction | Metadata and confirmation requests |

## Repository Layout

```text
med-data-auditor-skill/
|-- SKILL.md
|-- SPEC.md
|-- SOURCES.md
|-- README.md
|-- LICENSE
|-- requirements.txt
|-- run_audit.py
|-- core/
|-- data/
|-- examples/
|-- references/
|-- reports/
|-- rules/
|-- scripts/
`-- tests/
```

`SKILL.md` is the Agent Skills entrypoint. `run_audit.py` is a thin CLI wrapper. `core/orchestrator.py` controls the workflow, and `core/` contains the internal business modules and support layers. The original design draft is preserved in `med_data_auditor_skill_spec.md`.

## Limitations

This project is for educational and research data-auditing workflows only.

- Do not use it with identifiable patient data.
- Do not upload real patient data to external AI tools.
- It is not a clinical decision-making tool.
- It does not diagnose disease, recommend treatment, or validate clinical truth.
- It does not replace a statistician, clinical data manager, or regulatory-grade workflow.
- It does not implement full statistical modeling, visualization, web UI, LLM Council runtime, or automatic data cleaning. These remain out of scope for v0.2.0.
- All medical plausibility warnings require human confirmation.

## Roadmap

- v0.1.0 (complete): CSV audit, YAML rules, deterministic warnings, AI-ready report.
- v0.2.0 (complete): audit log, flagged records, unit warnings, missingness readiness, iterative extraction requests, report contract, and token metrics.
- v0.3: Table 1 readiness, logistic regression readiness, basic exploratory outputs, clinical trial demo data.
- v0.4+: Excel/SAS/Stata support, DuckDB, Great Expectations, CDISC concept checks, web UI.

v0.2.0 remains audit-first and warning-only. It does not clean data, impute values, convert units, fit models, or make clinical claims.

The GitHub portfolio version should keep the v0.2.0 identity focused: one main skill, deterministic local checks, privacy-safe structured outputs, and a professional AI-ready report.
