# Sources, Decisions, And Gaps

## Source Inventory

| Source | Trust | Contribution | Usage |
|---|---|---|---|
| `med_data_auditor_skill_spec.md` | High | Product intent, v0.1 scope, module list, safety boundaries, roadmap | Adapted into runtime skill, scripts, README, SPEC, and references |
| `skill-writer` local skill | High | Skill synthesis, authoring, description optimization, validation workflow | Used to choose workflow-process class and script-backed shape |
| `skill-creator` local skill | High | Agent Skills structure, frontmatter, validation, optional `agents/openai.yaml` | Used for `SKILL.md` and metadata shape |

## Synthesis Decisions

| Decision | Status | Rationale |
|---|---|---|
| Skill class: workflow-process | Adopted | The user needs a repeatable audit workflow with ordered checks and validation gates |
| Primary shape: script-backed workflow | Adopted | Data profiling, rule checks, and report generation must be deterministic and reusable |
| Runtime entrypoint: `SKILL.md` uppercase | Adopted | Agent Skills require `SKILL.md`; the source draft's lowercase `skill.md` was upgraded |
| Keep original design draft | Adopted | It is useful provenance and future planning material |
| External LLM API use | Rejected for v0.1 | The source requires local deterministic scanning and no external model calls |
| Web UI | Deferred | Out of v0.1 scope and would increase completion risk |

## Coverage Matrix

| Dimension | v0.1 Coverage |
|---|---|
| Preconditions | Privacy safety check and synthetic-data default |
| Ordered flow | CLI orchestrates profiling, variable mapping, medical checks, statistical checks, privacy checks, report rendering |
| Safety boundaries | No overwrite, no real patient data, no clinical decisions, warnings require confirmation |
| Expected outputs | AI-ready Markdown report plus sample data and tests |
| Failure handling | SKILL.md lists script fallbacks and asks for human confirmation on ambiguity |
| Validation | Sample data generation, CLI run, pytest, structural skill validator |

## Source Adaptation Notes

- Source intent: create a token-efficient biomedical data auditor suitable for future work and GitHub display.
- Local target: produce an installable Agent Skill repository plus a runnable Python CLI.
- Fidelity boundary: preserve v0.1 scope, safety limits, deterministic program/AI division, report sections, and roadmap.
- Local replacements: use `SKILL.md` instead of lowercase `skill.md`; split maintenance and provenance into `SPEC.md` and `SOURCES.md`.
- Omitted material: long narrative explanations from the design draft are not repeated in runtime files.

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

- v0.1 token metrics are rough estimates.
- Rules are generic and should be expanded with domain-specific validation cases.
- Variable role mapping is keyword-based and may need user confirmation.
- No flagged records CSV or audit log until v0.2.

## Changelog

- 2026-06-17: Created v0.1 repository structure, scripts, rules, references, tests, and skill metadata from the original design draft.
