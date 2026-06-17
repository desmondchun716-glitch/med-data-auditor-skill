# Med Data Auditor Skill

A token-efficient Python workflow for auditing biomedical and public health datasets before AI-assisted statistical analysis.

## Why This Project Matters

Large biomedical datasets are costly and unreliable for an AI assistant to inspect directly. This tool scans the full dataset locally, detects data quality and analysis-readiness risks, and generates a compact Markdown report that an AI assistant or human reviewer can use as evidence.

The project is intentionally small in v0.1: CSV input, pandas profiling, YAML rules, deterministic checks, and an AI-ready report. It does not clean the original data, make clinical decisions, or run production-grade clinical data management.

## Features

- CSV dataset profiling
- Missingness and duplicate patient ID detection
- Configurable medical plausibility checks
- Statistical analysis-readiness warnings
- Potential identifier and privacy field detection
- Question-driven exposure, outcome, and confounder mapping
- AI-ready Markdown audit report
- Synthetic sample data with injected quality issues
- Simple pytest coverage for the core checks

## Quick Start

```bash
pip install -r requirements.txt

python scripts/01_generate_sample_data.py

python scripts/run_audit.py \
  --data data/sample_medical_data.csv \
  --question "Is BMI associated with hypertension after adjusting for age and sex?" \
  --output reports/sample_audit_report.md
```

Open `reports/sample_audit_report.md` to review the generated audit.

## Example Use Case

User question:

```text
Is BMI associated with hypertension after adjusting for age and sex?
```

The auditor checks whether the dataset is ready for that analysis by reviewing key variables, BMI missingness, hypertension outcome balance, duplicate patient IDs, medical plausibility warnings, privacy-sensitive fields, and limitations such as association versus causation.

## Repository Layout

```text
med-data-auditor-skill/
├── SKILL.md
├── SPEC.md
├── SOURCES.md
├── README.md
├── requirements.txt
├── data/
├── examples/
├── references/
├── reports/
├── rules/
├── scripts/
└── tests/
```

`SKILL.md` is the Agent Skills entrypoint. The original design draft is preserved in `med_data_auditor_skill_spec.md`.

## Limitations

This project is for educational and research data-auditing workflows only.

- Do not use it with identifiable patient data.
- Do not upload real patient data to external AI tools.
- It is not a clinical decision-making tool.
- It does not replace a statistician, clinical data manager, or regulatory-grade workflow.
- All medical plausibility warnings require human confirmation.

## Roadmap

- v0.1: CSV audit, YAML rules, deterministic warnings, AI-ready report.
- v0.2: flagged records, audit logs, unit warnings, token metrics, iterative extraction requests.
- v0.3: Table 1 readiness, logistic regression readiness, basic exploratory outputs, clinical trial demo data.
- v0.4+: Excel/SAS/Stata support, DuckDB, Great Expectations, CDISC concept checks, web UI.
