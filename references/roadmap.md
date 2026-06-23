# Roadmap And Scope Control

Use this file before expanding beyond the current stable release.

Do not create separate skills for future categories. Add future directions as internal modules, scripts, rules, references, or roadmap items inside the single `med-data-auditor-skill` project.

## Current Stable Release

`v0.2.0` is the current stable portfolio release.

Completed:

- audit log contract
- flagged records contract
- unit warning contract
- missingness-readiness metrics
- iterative extraction protocol
- report contract and token metrics polish

Next:

- v0.3 planning only after v0.2.0 validation and tag.

## v0.1 Foundation

- CSV input
- pandas profiling
- YAML medical and statistical rules
- privacy field detection
- question-driven variable mapping
- basic study design warnings
- AI-ready Markdown report
- synthetic sample data
- simple tests
- CLI command

Internal structure:

- seven business modules in `core/`
- `core/schemas.py` for warning shape
- `core/orchestrator.py` for module order

The v0.1 foundation did not include full statistical modeling, visualization, web UI, LLM Council runtime, or automatic data cleaning. Those boundaries remain active in v0.2.0.

## v0.2.0 Completed Internal Workstreams

v0.2.0 remains inside the single `med-data-auditor-skill` architecture. Do not create child skills, new skill directories, or another `SKILL.md`.

All seven workstreams below are complete in v0.2.0. Future maintenance should preserve their contracts unless a new version explicitly revises scope.

### Workstream 1 - Single-skill guardrails and v0.2 contract

Purpose: encode v0.2 boundaries, the standard prompt header, branch and worktree coordination, and the PR checklist.

Allowed: documentation and contract updates only.

Primary files: `references/roadmap.md`, `SPEC.md`, `SOURCES.md`, and a tiny `SKILL.md` wording update if needed.

Not allowed: code changes, child skills, new skill directories, another `SKILL.md`, web UI, full statistical modeling, external LLM API calls, LLM Council, automatic data cleaning, or new domain modules.

### Workstream 2 - Audit log contract

Purpose: define and implement `audit_log.json` as a structured audit trail.

Implemented: deterministic local metadata, warning summaries, run timestamp, input/output paths, rule versions, missingness-readiness evidence, extraction requests, and token metrics.

Not allowed: storing real patient records, secrets, full raw datasets, or external LLM outputs as authoritative evidence.

### Workstream 3 - Flagged records contract

Purpose: define and implement `flagged_records.csv` for issue evidence.

Implemented: row index, issue ID, issue type, severity, variable, safe evidence summary, and human confirmation flag.

Not allowed: automatic biomedical correction, overwriting source data, or exposing sensitive identifiers.

### Workstream 4 - Unit warning contract

Purpose: add warnings for possible unit ambiguity in biomedical variables.

Implemented: warning-only checks for height, weight, glucose, creatinine, temperature, blood pressure, and similar fields, plus explicit human confirmation prompts.

Not allowed: automatic unit conversion without confirmation or treating unit guesses as clinical truth.

### Workstream 5 - Missingness and analysis-readiness metrics

Purpose: deepen missingness and key-variable risk summaries.

Implemented: missingness by variable role, row-level burden, near-empty columns, key-variable complete cases, co-occurrence summaries, and model-readiness warnings.

Not allowed: multiple imputation, fitted models, causal inference, or p-value-driven conclusions.

### Workstream 6 - Iterative extraction protocol

Purpose: define local deterministic request/response summaries that an AI assistant can ask for after reading the audit report.

Implemented: metadata-only requests for variable roles, units, coding, missingness, study design, privacy, repeated measures, population, and time windows.

Not allowed: external LLM API calls, AI inspection of raw rows, uncontrolled query execution, or natural-language SQL over raw private data.

### Workstream 7 - Report contract and token metrics polish

Purpose: improve report consistency, token compression summaries, and portfolio readability.

Implemented: stable 13-section report order, deterministic approximate token estimates, and stronger limitations wording.

Not allowed: automatic paper writing, full modeling, visualization, or clinical recommendations.

## v0.2.0 Explicit Non-goals

The following are not allowed in v0.2.0:

- child skills
- another `SKILL.md`
- another skill directory
- web UI
- full statistical modeling
- external LLM API calls
- LLM Council
- automatic data cleaning or biomedical correction
- new domain modules such as clinical trial, RWE, questionnaire, CDISC, or survey-specific modules
- real patient data support

## Standard Codex Prompt Header

Use this header at the start of every v0.2.0 maintenance task:

```text
Project: med-data-auditor-skill
Repo: desmondchun716-glitch/med-data-auditor-skill
Version target: v0.2.0 maintenance
Architecture rule: one main Agent Skill only.

Active maintenance goal:
- <maintenance goal>

Branch:
- codex/v0.2/<short-slug>

Allowed files:
- <list exact files>

Forbidden changes:
- Do not create child skills.
- Do not create another SKILL.md.
- Do not create another skill directory.
- Do not add web UI.
- Do not add full statistical modeling.
- Do not add external LLM API calls.
- Do not add LLM Council.
- Do not add automatic data cleaning.
- Do not add new domain modules.
- Do not modify the existing core pipeline unless explicitly required.

Goal:
- <one sentence goal>

Validation:
- Show changed files.
- Confirm no child skills or extra SKILL.md were created.
- Run existing tests if code changed.
```

## Branch And Worktree Coordination Rule

Use one branch per maintenance goal.

Branch naming:

```text
codex/v0.2/<short-slug>
```

Examples:

```text
codex/v0.2/docs-release-consistency
codex/v0.2/contract-polish
codex/v0.2/sample-output-refresh
```

Rules:

- Do not run two Codex sessions on the same branch.
- Do not let two Codex sessions edit the same file at the same time.
- Use separate git worktrees for parallel maintenance goals.
- Documentation-only maintenance should not change `core/`, `rules/`, `scripts/`, `tests/`, `data/`, `reports/`, or `examples/` unless a tracked sample output or stale runtime wording is intentionally refreshed.
- Code-changing maintenance must include validation output.
- Each PR must state its active maintenance goal and forbidden changes checked.

## v0.2 PR Checklist

Every v0.2.0 maintenance PR must include:

- [ ] Active maintenance goal is named.
- [ ] Branch follows `codex/v0.2/<short-slug>`.
- [ ] No child skill was created.
- [ ] No extra `SKILL.md` was created.
- [ ] No new skill directory was created.
- [ ] No web UI was added.
- [ ] No full statistical modeling was added.
- [ ] No external LLM API call was added.
- [ ] No LLM Council was added.
- [ ] No automatic data cleaning or biomedical correction was added.
- [ ] No new domain module was added.
- [ ] Existing CLI behavior remains backward compatible unless the PR explicitly explains why.
- [ ] Changed files are listed.
- [ ] Validation commands or rationale are included.

## v0.3 Next Planned Phase

- Table 1 readiness
- exploratory Table 1 generation
- logistic regression readiness
- basic OR / 95% CI output with strong limitations
- public health questionnaire module
- clinical trial demo module

## v0.4+ Candidates

- Excel, SAS, and Stata support
- DuckDB integration
- Great Expectations integration
- multi-file cohort linkage
- CDISC SDTM / ADaM concept checker
- web interface
- LLM Council-style structured-output review

## Expansion Gate

Before adding a feature, confirm:

1. It does not weaken privacy safety.
2. It has a deterministic validation path.
3. It improves analysis readiness rather than becoming generic cleaning.
4. It does not require external LLM calls for core auditing.
5. It keeps warnings separate from clinical conclusions.
6. It stays inside the one-skill architecture.
