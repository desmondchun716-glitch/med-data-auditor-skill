# Roadmap And Scope Control

Use this file before expanding beyond the first version.

## v0.1 Only

- CSV input
- pandas profiling
- YAML medical and statistical rules
- privacy field detection
- question-driven variable mapping
- AI-ready Markdown report
- synthetic sample data
- simple tests
- CLI command

## v0.2 Candidates

- `flagged_records.csv`
- `audit_log.json`
- unit warnings
- study design warning
- missingness mechanism screening
- iterative extraction requests
- token compression metrics

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

## Expansion Gate

Before adding a feature, confirm:

1. It does not weaken privacy safety.
2. It has a deterministic validation path.
3. It improves analysis readiness rather than becoming generic cleaning.
4. It does not require external LLM calls for core auditing.
5. It keeps warnings separate from clinical conclusions.
