# Med Data Auditor Skill

Token-efficient biomedical data analysis-readiness auditing for CSV datasets.

This is not a generic data cleaning script. It is an audit-first workflow that scans biomedical and public health datasets locally, detects analysis-readiness risks, and produces a compact AI-ready Markdown report before any modeling or interpretation.

## Overview

Med Data Auditor Skill profiles biomedical and public health datasets locally, detects data quality issues, biomedical plausibility problems, statistical analysis risks, and privacy concerns, then generates compact AI-ready Markdown reports for iterative analysis.

The v0.1 promise is narrow and concrete:

```text
CSV + biomedical research question -> AI-ready analysis-readiness audit report
```

## Why This Project Matters

Large biomedical datasets are costly and unreliable for an AI assistant to inspect directly. This tool scans the full dataset locally, detects data quality and analysis-readiness risks, and generates a compact Markdown report that an AI assistant or human reviewer can use as evidence.

The project is intentionally small in v0.1: CSV input, pandas profiling, YAML rules, deterministic checks, and an AI-ready report. It does not clean the original data, make clinical decisions, or run production-grade clinical data management.

This repository contains one main skill named `med-data-auditor-skill`. Future directions should become internal modules or roadmap items after the core workflow is strong enough, not separate skills.

## Core Idea

Programmatic scanning first, AI interpretation second. The program scans the full dataset locally; the AI reads only the compressed evidence report; the human confirms warnings before analysis decisions.

## What v0.1 Does Not Do

- No automatic data cleaning
- No fitted statistical models
- No odds ratios, p-values, or confidence intervals
- No visualization or web UI
- No external LLM API calls
- No LLM Council or multi-agent review layer
- No new domain modules

## Features

- CSV dataset profiling
- Missingness and duplicate patient ID detection
- Configurable medical plausibility checks
- Warning-only checks for possible biomedical unit or scale mismatches
- Statistical analysis-readiness warnings
- Potential identifier and privacy field detection
- Question-driven exposure, outcome, and confounder mapping
- AI-ready Markdown audit report
- Optional privacy-safe machine-readable audit log JSON
- Optional privacy-safe flagged records CSV for row-level warning references
- Synthetic sample data with injected quality issues
- Simple pytest coverage for the core checks

## What It Checks

- Data intake and file metadata
- Data profiling and type detection
- Biomedical plausibility warnings
- Possible unit mismatches for explicitly labeled blood pressure, temperature, percent/fraction, height, weight, glucose, creatinine, and lipid fields
- Statistical analysis-readiness risks
- Variable role mapping and basic study design warnings
- Privacy / PII fields and small-cell risk
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

Example CLI output:

```text
Wrote audit report to reports/sample_audit_report.md
Wrote audit log to reports/sample_audit_log.json
Wrote flagged records to reports/sample_flagged_records.csv
Warnings: intake=0, medical=7, statistical=6, privacy=2, study_design=0
Approximate token compression: 9236 -> 2130 (4.3:1)
```

## Example Use Case

User question:

```text
Is BMI associated with hypertension after adjusting for age and sex?
```

The auditor checks whether the dataset is ready for that analysis by reviewing key variables, BMI missingness, hypertension outcome balance, duplicate patient IDs, medical plausibility warnings, privacy-sensitive fields, and limitations such as association versus causation.

## Example Output

See `reports/sample_audit_report.md`.

Synthetic demo issue coverage:

| Injected issue | Detected in sample report |
|---|---:|
| Age range outlier rows | 2 |
| BMI range outlier rows | 2 |
| Duplicate patient ID rows | 3 |
| SBP lower than DBP rows | 1 |
| Death date before visit date rows | 1 |
| Negative follow-up rows | 1 |

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
- It does not implement full statistical modeling, visualization, web UI, LLM Council, or automatic data cleaning in v0.1.
- All medical plausibility warnings require human confirmation.

## Roadmap

- v0.1: CSV audit, YAML rules, deterministic warnings, AI-ready report.
- v0.2: flagged records, audit logs, unit warnings, expanded audit metrics, iterative extraction requests.
- WS4 unit warnings are deterministic and warning-only; they never convert values or modify the source dataset.
- v0.3: Table 1 readiness, logistic regression readiness, basic exploratory outputs, clinical trial demo data.
- v0.4+: Excel/SAS/Stata support, DuckDB, Great Expectations, CDISC concept checks, web UI.

The GitHub portfolio version should keep the v0.1 scope narrow: one main skill, deterministic local checks, and a professional AI-ready report.
