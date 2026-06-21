# Missingness And Analysis-Readiness Contract

## Purpose

WS5 adds deterministic missingness evidence that helps a human reviewer decide whether a biomedical or public health dataset is ready for a statistical analysis plan.

WS5 measures and warns about missingness and analysis-readiness risk. It does not impute, clean, model, or decide missingness mechanisms.

## Scope

The implementation may compute:

- dataset-level missing counts and rates
- row-level missingness burden
- complete-case counts and rates for mapped exposure, outcome, and confounder variables
- near-empty column indicators
- top co-occurring missingness pairs
- transparent readiness flags
- privacy-safe example row indexes for warnings

The implementation may render these metrics through the existing Markdown report and `audit_log.json` dataset summary. Warnings may flow into the existing `flagged_records.csv` output through their `example_rows`.

## Non-goals

WS5 does not:

- impute values
- mutate the source DataFrame
- drop rows or columns
- create a cleaned dataset
- fit statistical models
- recommend a specific imputation method
- classify missingness as MCAR, MAR, or MNAR
- perform sensitive subgroup missingness analysis
- implement WS6 or WS7

## Metrics Contract

`build_missingness_readiness_metrics(...)` returns counts, rates, column names, thresholds, caveat text, and transparent boolean or string flags.

The public metrics include:

- dataset shape and overall missing-cell rate
- columns with any, high, critical, or near-empty missingness
- rows with any missingness and rows with high missingness burden
- complete rows across all columns
- mapped key variables and their complete-case readiness
- top missing columns
- top missingness co-occurrence pairs
- mechanism-screening indicators
- readiness flags

No raw cell values or full rows are returned.

## Warning Contract

`check_missingness_readiness(...)` returns warnings through the existing `make_warning()` helper.

Requirements:

- issue IDs start with `MISS_`
- issue types remain `data_quality` or `statistical_risk`
- wording is cautious and requests review or confirmation
- warnings may contain counts, rates, column names, and example row indexes
- warnings do not contain raw cell values
- warnings require human confirmation

## Privacy Boundary

Allowed evidence:

- column names
- counts and rates
- row indexes
- complete-case counts
- co-occurrence counts
- readiness flags

Forbidden evidence:

- raw patient values
- full rows
- direct identifier values
- free-text clinical notes
- secrets
- sensitive small-group breakdowns

## Missingness Mechanism Caveat

Missingness mechanism screening is evidence triage, not diagnosis. Structured, clustered, or analysis-threatening missingness should trigger human review, not an automated MCAR, MAR, or MNAR label.

## Output Behavior

- The Markdown report adds compact readiness subsections under `## 5. Missing Data Summary`.
- The audit log stores the metrics inside `dataset_summary.missingness_readiness`.
- No new audit-log top-level key is added.
- Flagged-record schema remains unchanged.
- No new output file is introduced.

## Validation Rules

Validation must confirm:

- deterministic metrics
- no DataFrame mutation
- valid warning schema
- no raw-value leakage
- role-aware complete-case calculation
- safe co-occurrence summaries
- report generation
- audit-log schema validation
- flagged-record integration
- full pytest success
