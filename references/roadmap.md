# Roadmap And Scope Control

Use this file before expanding beyond the first version.

Do not create separate skills for future categories. Add future directions as internal modules, scripts, rules, references, or roadmap items inside the single `med-data-auditor-skill` project.

## v0.1 Only

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

Do not add full statistical modeling, visualization, web UI, LLM Council, or automatic data cleaning in v0.1.

## v0.2 Internal Workstreams

v0.2 must remain inside the single `med-data-auditor-skill` architecture. Do not create child skills, new skill directories, or another `SKILL.md`.

### Workstream 1 - Single-skill guardrails and v0.2 contract

Purpose: encode v0.2 boundaries, the standard prompt header, branch and worktree coordination, and the PR checklist.

Allowed: documentation and contract updates only.

Primary files: `references/roadmap.md`, `SPEC.md`, `SOURCES.md`, and a tiny `SKILL.md` wording update if needed.

### Workstream 2 - Audit log contract

Purpose: define and later implement `audit_log.json` as a structured audit trail.

Allowed later: deterministic local metadata, warning summaries, run timestamp, input/output paths, and rule versions.

Not allowed: storing real patient records, secrets, or full raw datasets.

### Workstream 3 - Flagged records contract

Purpose: define and later implement `flagged_records.csv` for issue evidence.

Allowed later: row index, issue ID, variable, severity, issue type, and safe evidence summary.

Not allowed: automatic biomedical correction or overwriting source data.

### Workstream 4 - Unit warning contract

Purpose: add warnings for possible unit ambiguity in biomedical variables.

Allowed later: warning-only checks for height, weight, glucose, creatinine, temperature, blood pressure, and similar fields.

Not allowed: automatic unit conversion unless the user explicitly confirms the intended units.

### Workstream 5 - Missingness and analysis-readiness metrics

Purpose: deepen missingness and key-variable risk summaries.

Allowed later: missingness by variable role, outcome imbalance detail, sparse category detail, and simple missingness-by-group summaries.

Not allowed: multiple imputation, fitted models, causal inference, or p-value-driven conclusions.

### Workstream 6 - Iterative extraction protocol

Purpose: define local deterministic request/response summaries that an AI assistant can ask for after reading the audit report.

Allowed later: grouped summaries, missingness summaries, value counts, and mean/SD summaries.

Not allowed: external LLM API calls or AI inspection of raw rows.

### Workstream 7 - Report contract and token metrics polish

Purpose: improve report consistency, token compression summaries, and portfolio readability.

Allowed later: clearer report sections, deterministic token estimates, and stronger limitations wording.

Not allowed: automatic paper writing, full modeling, visualization, or clinical recommendations.

## v0.2 Explicit Non-goals

The following are not allowed in v0.2:

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

Use this header at the start of every v0.2 Codex task:

```text
Project: med-data-auditor-skill
Repo: desmondchun716-glitch/med-data-auditor-skill
Version target: v0.2
Architecture rule: one main Agent Skill only.

Active workstream:
- WS<number>: <workstream name>

Branch:
- codex/v0.2/ws<number>-<short-slug>

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

Use one branch per workstream.

Branch naming:

```text
codex/v0.2/ws<number>-<short-slug>
```

Examples:

```text
codex/v0.2/ws1-contract-guardrails
codex/v0.2/ws2-audit-log-contract
codex/v0.2/ws3-flagged-records-contract
```

Rules:

- Do not run two Codex sessions on the same branch.
- Do not let two Codex sessions edit the same file at the same time.
- Use separate git worktrees for parallel workstreams.
- Merge Workstream 1 before implementation-heavy v0.2 workstreams.
- Documentation-only workstreams should not change `core/`, `rules/`, `scripts/`, `tests/`, `data/`, or `reports/`.
- Code-changing workstreams must include validation output.
- Each PR must state its active workstream and forbidden changes checked.

## PR Checklist

Every v0.2 PR must include:

- [ ] Active workstream is named.
- [ ] Branch follows `codex/v0.2/ws<number>-<short-slug>`.
- [ ] No child skill was created.
- [ ] No extra `SKILL.md` was created.
- [ ] No new skill directory was created.
- [ ] No web UI was added.
- [ ] No full statistical modeling was added.
- [ ] No external LLM API call was added.
- [ ] No LLM Council was added.
- [ ] No automatic data cleaning or biomedical correction was added.
- [ ] No new domain module was added.
- [ ] Existing v0.1 CLI behavior remains unchanged unless the PR explicitly explains why.
- [ ] Changed files are listed.
- [ ] Validation commands or rationale are included.

## v0.3 Candidates

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
