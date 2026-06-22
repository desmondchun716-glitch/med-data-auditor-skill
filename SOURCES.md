# Sources, Decisions, And Gaps

## Source Inventory

| Source | Trust | Contribution | Usage |
|---|---|---|---|
| `med_data_auditor_skill_spec.md` | High | Product intent, v0.1 scope, module list, safety boundaries, roadmap | Adapted into runtime skill, scripts, README, SPEC, and references |
| `med_data_auditor_skill_complete_blueprint.md` | High | Latest one-skill architecture, seven internal modules, schemas/orchestrator layers, study design warnings, PII/small-cell privacy notes | Adapted into `core/` modules, docs, report contract, and roadmap |
| `skill-writer` local skill | High | Skill synthesis, authoring, description optimization, validation workflow | Used to choose workflow-process class and script-backed shape |
| `skill-creator` local skill | High | Agent Skills structure, frontmatter, validation, optional `agents/openai.yaml` | Used for `SKILL.md` and metadata shape |
| `WS6 LLM Council + Codex Implementation Plan` | High | Iterative extraction schema, triggers, privacy boundary, integration points, tests, and release checklist | Adapted into deterministic local code and contract documentation; council content was planning only |
| `WS7 LLM Council + Codex Implementation Plan` | High | Final v0.2 report order, token metric shape, privacy boundaries, tests, and release checklist | Adapted into the report contract, local token metrics helper, audit-log validation, and regression tests; council content was planning only |

## Synthesis Decisions

| Decision | Status | Rationale |
|---|---|---|
| Skill class: workflow-process | Adopted | The user needs a repeatable audit workflow with ordered checks and validation gates |
| Primary shape: script-backed workflow | Adopted | Data profiling, rule checks, and report generation must be deterministic and reusable |
| Runtime entrypoint: `SKILL.md` uppercase | Adopted | Agent Skills require `SKILL.md`; the source draft's lowercase `skill.md` was upgraded |
| Keep original design draft | Adopted | It is useful provenance and future planning material |
| External LLM API use | Rejected for v0.1 | The source requires local deterministic scanning and no external model calls |
| Web UI | Deferred | Out of v0.1 scope and would increase completion risk |
| Eight separate skill categories | Rejected | Future categories should be internal modules or roadmap items inside one main skill |
| GitHub upload | Completed | Published after v0.1 workflow polish, validation, and user approval |
| `core/` module architecture | Adopted | The latest blueprint clarifies seven business modules and two support layers |
| Basic study design warnings | Adopted for v0.1 | Warnings support analysis readiness without performing modeling |
| v0.2 as internal workstreams | Adopted | Keeps future work inside one main skill and prevents Codex from creating child skills |
| Standard Codex prompt header | Adopted | Makes future task boundaries explicit before each Codex session |
| One branch per workstream | Adopted | Reduces merge conflicts and prevents overlapping Codex edits |
| v0.2 PR checklist | Adopted | Provides a lightweight release gate for portfolio-quality maintenance |
| Documentation-only Workstream 1 | Adopted | Protects the v0.1 pipeline while setting up future implementation workstreams |
| WS2 audit log contract | Adopted | Adds a privacy-safe machine-readable audit trail without storing raw patient data |
| WS3 flagged records contract | Adopted | Adds an optional row-reference issue index without exporting raw patient data |
| WS4 warning-only unit checks | Adopted | Adds conservative deterministic unit-risk evidence without conversion, raw-value leakage, or schema expansion |
| WS5 missingness readiness evidence | Adopted | Adds role-aware complete-case, row-burden, near-empty-column, and co-occurrence metrics without imputation or missingness-mechanism classification |
| WS6 metadata-only iterative extraction protocol | Adopted | Converts existing audit evidence into safe, prioritized human questions without raw-data extraction, external calls, or dataset mutation |
| New WS6 output file or CLI flag | Rejected | The Markdown report and existing audit-log analysis context already provide the needed human and machine-readable surfaces |
| LLM Council runtime | Rejected | The council was a planning framework only; runtime behavior remains deterministic Python |
| WS7 stable report contract | Adopted | Locks the existing 13-section report order and compact evidence policy without adding a new output |
| Character-based token metrics | Adopted | Improves transparency and audit traceability without an external tokenizer dependency or exact-token claim |
| New WS7 output or CLI flag | Rejected | Existing report, audit log, and flagged-record outputs are sufficient |

## Coverage Matrix

| Dimension | v0.1 Coverage |
|---|---|
| Preconditions | Privacy safety check and synthetic-data default |
| Ordered flow | CLI calls `core/orchestrator.py`, which runs intake, profiling, mapping, study design, medical checks, statistical checks, privacy checks, and report rendering |
| Safety boundaries | No overwrite, no real patient data, no clinical decisions, warnings require confirmation |
| Expected outputs | AI-ready Markdown report plus sample data and tests |
| Failure handling | SKILL.md lists script fallbacks and asks for human confirmation on ambiguity |
| Validation | Sample data generation, CLI run, pytest, structural skill validator |
| Iterative extraction | Deterministic request schema, grouped evidence triggers, privacy-safe guidance, report rendering, and audit-log nesting under `analysis_context` |

## Source Adaptation Notes

- Source intent: create a token-efficient biomedical data auditor suitable for future work and eventual portfolio display.
- Local target: produce an installable Agent Skill repository plus a runnable Python CLI.
- Fidelity boundary: preserve v0.1 scope, safety limits, deterministic program/AI division, report sections, and roadmap.
- Local replacements: use `SKILL.md` instead of lowercase `skill.md`; use `core/` internal modules instead of separate skills; split maintenance and provenance into `SPEC.md` and `SOURCES.md`.
- Omitted material: long narrative explanations from the design draft are not repeated in runtime files.
- WS6 source intent: turn audit findings into safe questions about metadata and confirmations before analysis.
- WS6 fidelity boundary: preserve request schema, priority, deduplication, privacy, report, and audit-log behavior while omitting any LLM Council runtime or automated extraction.

## Description Optimization

Should trigger:

- "Audit this biomedical CSV before analysis."
- "Check whether this public health dataset is ready for AI-assisted analysis."
- "Detect medical plausibility and statistical risks in this RWE dataset."
- "Generate an AI-ready audit report for a hypertension research question."

Should not trigger:

- "Clean this generic sales CSV."
- "Build a web dashboard."
- "Write a clinical diagnosis."
- "Run a full causal inference analysis and publish a paper."

Final description emphasizes health-related datasets, local audit tasks, and report generation while excluding generic data cleaning by context.

## Open Gaps

- Token metrics remain approximate character-based engineering estimates and must not be interpreted as exact tokenizer counts.
- Rules are generic and should be expanded with domain-specific validation cases.
- Variable role mapping is keyword-based and may need user confirmation.
- WS3 flagged records are implemented as an optional CSV output; future work should keep the contract privacy-safe.
- Future Codex sessions must include the standard prompt header to avoid scope drift.
- All seven v0.2 workstreams are implemented; release tagging remains a separate post-merge step.

## Changelog

- 2026-06-17: Created v0.1 repository structure, scripts, rules, references, tests, and skill metadata from the original design draft.
- 2026-06-17: Tightened scope to one main skill and deferred new feature work until after v0.1 approval.
- 2026-06-17: Adapted latest complete blueprint into a `core/` internal-module architecture with schemas, orchestrator, study design warnings, and stronger privacy checks.
- 2026-06-17: Published the polished v0.1 repository to GitHub and kept future expansion in the roadmap.
- 2026-06-17: Added v0.2 single-skill guardrails, seven internal workstreams, standard Codex prompt header, branch/worktree coordination rule, and PR checklist.
- 2026-06-17: Added WS2 audit log contract and optional privacy-safe `audit_log.json` output implementation.
- 2026-06-17: Added WS3 flagged records contract and optional privacy-safe `flagged_records.csv` output implementation.
- 2026-06-21: Added WS4 deterministic warning-only checks for possible biomedical unit and scale mismatches.
- 2026-06-21: Added WS5 deterministic, privacy-safe missingness and analysis-readiness metrics.
- 2026-06-21: Added WS6 deterministic, privacy-safe iterative extraction requests in the report and audit-log analysis context.
- 2026-06-22: Finalized the WS7 v0.2 report contract, runtime wording, approximate token metrics, audit-log validation, and regression tests.
