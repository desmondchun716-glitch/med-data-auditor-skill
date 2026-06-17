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
- Question-driven exposure, outcome, and confounder mapping
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

## Users And Trigger Context

- Primary users: biomedical, public health, clinical research, RWE, CRO, MCM/ICM, and health survey learners or analysts.
- Common requests: "audit this medical dataset", "check if this CSV is ready for analysis", "summarize data quality before AI analysis", "is this dataset ready to study BMI and hypertension".
- Should not trigger for: non-health generic data cleaning unless the user explicitly asks for biomedical-style analysis-readiness auditing.

## Runtime Contract

- Required first actions: verify privacy safety, run local scripts when a CSV is available, read the Markdown report before advising.
- Required outputs: report with dataset overview, relevant variables, missingness, medical warnings, statistical warnings, privacy warnings, analysis-readiness notes, human confirmation questions, token-saving summary, and limitations.
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
- `scripts/` contains deterministic data generation, profiling, checking, mapping, and report rendering code.
- `rules/` contains YAML medical, statistical, and variable dictionary configuration.
- `tests/` contains lightweight regression checks for the first version.

## Validation

- Lightweight validation: run sample data generation, full audit CLI, pytest, and skill structural validator.
- Deeper validation: run against additional synthetic health survey, RWE, and clinical trial-like CSVs.
- Holdout examples: future versions should keep small de-identified or synthetic edge-case fixtures.
- Acceptance gates: one-command audit works, injected issues are detected, report includes all required sections, and safety limitations are visible.

## Known Limitations

- Variable role mapping uses keyword matching, not advanced NLP.
- Medical plausibility rules are generic and require human confirmation.
- Statistical risk checks are readiness warnings, not formal modeling.
- Token estimates are rough in v0.1.

## Maintenance Notes

- Update `SKILL.md` when runtime workflow, trigger language, safety rules, or validation commands change.
- Update `SOURCES.md` when decisions, gaps, source material, or validation evidence change.
- Update `references/` when optional report, rule, or roadmap guidance becomes too detailed for `SKILL.md`.
