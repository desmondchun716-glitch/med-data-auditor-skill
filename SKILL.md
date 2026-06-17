---
name: med-data-auditor-skill
description: Audits biomedical, clinical, public health, epidemiology, health survey, RWE, and medical research CSV datasets before AI-assisted statistical analysis. Use when a user provides or references a health-related dataset and asks to profile data, detect missingness, duplicate IDs, medical plausibility issues, privacy fields, statistical analysis-readiness risks, or generate an AI-ready Markdown audit report for a research question.
---

# Med Data Auditor Skill

## Single Skill Boundary

Use exactly one main skill named `med-data-auditor-skill`. Treat future categories as internal modules or roadmap items, not separate skills.

For v0.1, implement only the core analysis-readiness audit workflow: data intake, data profiling, biomedical plausibility checks, statistical risk checks, variable role mapping, privacy / PII field detection, and AI-ready Markdown report generation.

## Default Workflow

1. Confirm the data is synthetic, de-identified, or safe for local processing. Do not upload identifiable patient data to external services.
2. Run the local audit pipeline instead of asking the AI to inspect raw rows manually:

```bash
python run_audit.py --data <csv_path> --question "<research question>" --output reports/audit_report.md
```

3. Read the generated Markdown report before giving analysis advice.
4. Base recommendations on the report evidence: key variables, missingness, duplicates, plausibility warnings, privacy warnings, and statistical risks.
5. Ask the user to confirm ambiguous variable meanings and any critical medical plausibility warnings before proceeding to analysis.

## Internal Module Contract

| Module | Role |
|---|---|
| `core/intake.py` | Load CSV data safely and capture file metadata without modifying raw data |
| `core/profiler.py` | Generate compact dataset profile, missingness, types, duplicates, and ID-like columns |
| `core/variable_mapper.py` | Map question terms to exposure, outcome, confounders, and study design warnings |
| `core/medical_rules.py` | Detect biomedical plausibility and data-quality warnings |
| `core/statistical_risks.py` | Detect analysis-readiness risks before modeling |
| `core/privacy_checker.py` | Detect privacy / PII fields and small-cell risks |
| `core/report_generator.py` | Render the AI-ready Markdown report |
| `core/schemas.py` | Define shared warning schema and issue categories |
| `core/orchestrator.py` | Control module order and produce the final report |

## Script Contract

| Script | Use | Output | Fallback |
|---|---|---|---|
| `scripts/generate_sample_data.py` | Create synthetic demo data with injected issues | `data/sample_medical_data.csv` | Create a small synthetic CSV manually, never real patient data |
| `run_audit.py` | Run the full audit | Markdown report at `--output` | Call `core/orchestrator.py` directly and summarize results |
| `scripts/*.py` compatibility wrappers | Preserve earlier script imports and commands | Delegates to `core/` modules | Use the corresponding `core/` module |

## Runtime Rules

- Never overwrite the original dataset.
- Treat warnings as evidence for review, not proof that records are wrong.
- Keep deterministic checks in Python and interpretation in the AI response.
- Do not split this project into multiple skills.
- Do not make causal, clinical, or regulatory claims.
- Do not implement full statistical modeling, visualization, web UI, LLM Council, or automatic data cleaning in v0.1.
- Prefer association language unless study design and analysis justify stronger wording.
- If the report is missing key variables or has critical warnings, stop and ask for human confirmation before modeling advice.

## References

- Read `references/report-contract.md` before changing report sections, warning schemas, or token-saving summaries.
- Read `references/rules-guide.md` before adding or changing YAML rules.
- Read `references/roadmap.md` before expanding beyond v0.1 scope.
- Read `SPEC.md` when maintaining scope, validation expectations, or evidence policy.
- Read `SOURCES.md` when checking provenance, decisions, gaps, and changelog history.

## Validation

Run these checks after modifying the skill or scripts:

```bash
python scripts/generate_sample_data.py
python run_audit.py --data data/sample_medical_data.csv --question "Is BMI associated with hypertension after adjusting for age and sex?" --output reports/sample_audit_report.md
python -m pytest
```

If an Agent Skills structural validator is available, run it against this skill directory before publishing.
