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

## Users And Trigger Context

- Primary users: biomedical, public health, clinical research, RWE, CRO, MCM/ICM, and health survey learners or analysts.
- Common requests: "audit this medical dataset", "check if this CSV is ready for analysis", "summarize data quality before AI analysis", "is this dataset ready to study BMI and hypertension".
- Should not trigger for: non-health generic data cleaning unless the user explicitly asks for biomedical-style analysis-readiness auditing.

## Runtime Contract

- Required first actions: verify privacy safety, run the local orchestrator when a CSV is available, read the Markdown report before advising.
- Required outputs: report with dataset overview, relevant variables and study design, missingness, biomedical warnings, statistical warnings, privacy / PII warnings, analysis-readiness notes, human confirmation questions, token-saving summary, and limitations.
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
- `references/` contains report contracts, rule authoring guidance, and roadmap scope control for one main skill.
- `core/` contains seven business modules plus `schemas.py` and `orchestrator.py`.
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
python -m pytest
```

The PR must explain if any command is not run.

## Known Limitations

- Variable role mapping uses keyword matching, not advanced NLP.
- Medical plausibility rules are generic and require human confirmation.
- Statistical risk checks are readiness warnings, not formal modeling.
- Token estimates are rough in v0.1.

## Maintenance Notes

- Update `SKILL.md` when runtime workflow, trigger language, safety rules, or validation commands change.
- Update `SOURCES.md` when decisions, gaps, source material, or validation evidence change.
- Update `references/` when optional report, rule, or roadmap guidance becomes too detailed for `SKILL.md`.
