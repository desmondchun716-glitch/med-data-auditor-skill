---
name: med-data-auditor-skill
description: Audits biomedical, clinical, public health, epidemiology, health survey, RWE, and medical research CSV datasets before AI-assisted statistical analysis. Use when a user provides or references a health-related dataset and asks to profile data, detect missingness, duplicate IDs, medical plausibility issues, privacy fields, statistical analysis-readiness risks, or generate an AI-ready Markdown audit report for a research question.
---

# Med Data Auditor Skill

## Default Workflow

1. Confirm the data is synthetic, de-identified, or safe for local processing. Do not upload identifiable patient data to external services.
2. Run the local audit pipeline instead of asking the AI to inspect raw rows manually:

```bash
python scripts/run_audit.py --data <csv_path> --question "<research question>" --output reports/audit_report.md
```

3. Read the generated Markdown report before giving analysis advice.
4. Base recommendations on the report evidence: key variables, missingness, duplicates, plausibility warnings, privacy warnings, and statistical risks.
5. Ask the user to confirm ambiguous variable meanings and any critical medical plausibility warnings before proceeding to analysis.

## Script Contract

| Script | Use | Output | Fallback |
|---|---|---|---|
| `scripts/01_generate_sample_data.py` | Create synthetic demo data with injected issues | `data/sample_medical_data.csv` | Create a small synthetic CSV manually, never real patient data |
| `scripts/run_audit.py` | Run the full audit | Markdown report at `--output` | Run module scripts separately and summarize results |
| `scripts/02_profile_data.py` | Profile rows, columns, types, missingness, duplicates | Python dict | Use pandas profiling snippets locally |
| `scripts/03_rule_checks.py` | Apply medical plausibility and logic rules | Warning list | Inspect `rules/medical_rules.yaml` and run checks manually |
| `scripts/04_statistical_risk_checks.py` | Detect analysis-readiness risks | Warning list | Report missingness/outcome/sparsity limits manually |
| `scripts/05_relevant_variables.py` | Map question terms to exposure, outcome, confounders | Role mapping dict | Ask the user to confirm variable roles |
| `scripts/06_privacy_checks.py` | Detect potential identifier fields | Warning list | Manually scan column names for direct identifiers |
| `scripts/07_generate_report.py` | Render the AI-ready Markdown report | Markdown string | Use `references/report-contract.md` as the report template |

## Runtime Rules

- Never overwrite the original dataset.
- Treat warnings as evidence for review, not proof that records are wrong.
- Keep deterministic checks in Python and interpretation in the AI response.
- Do not make causal, clinical, or regulatory claims.
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
python scripts/01_generate_sample_data.py
python scripts/run_audit.py --data data/sample_medical_data.csv --question "Is BMI associated with hypertension after adjusting for age and sex?" --output reports/sample_audit_report.md
python -m pytest
```

If an Agent Skills structural validator is available, run it against this skill directory before publishing.
