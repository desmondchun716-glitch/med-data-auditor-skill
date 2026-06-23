# AI-ready Biomedical Data Audit Report

## 1. User Question

Is BMI associated with hypertension after adjusting for age and sex?

## 2. Executive Summary

**Readiness verdict:** Not ready for modeling: review critical and high-priority audit findings first.

This v0.2 audit scanned the full CSV locally and generated a compact evidence report for biomedical analysis-readiness review. It did not clean the data, fit statistical models, call external LLM APIs, or make clinical decisions.

**Warning summary**

| Critical | High | Medium | Low | Info |
|---:|---:|---:|---:|---:|
| 7 | 4 | 7 | 0 | 0 |

**Priority findings**

- `MED_DUPLICATE_PATIENT_ID` on `patient_id` (3 affected rows): Duplicate patient_id values were detected.
- `MED_LOGIC_001` on `sbp, dbp` (1 affected row): Systolic blood pressure should not be lower than diastolic blood pressure.
- `MED_LOGIC_002` on `death_date, visit_date` (1 affected row): Death date should not be earlier than visit date.
- `MED_LOGIC_003` on `follow_up_days` (1 affected row): Follow-up time should not be negative.
- `MED_RANGE_AGE` on `age` (2 affected rows): Age should be between 0 and 120 years.
- `PRIV_DIRECT_IDENTIFIER` on `patient_name`: Potential direct identifier field detected.

## 3. Dataset Overview

- Rows: 300
- Columns: 18
- Variable type summary: 6 categorical, 2 date, 3 identifier-like, 7 numeric
- Potential ID columns: `patient_id`, `patient_name`, `email`
- Duplicate rows: 0
- Duplicate patient ID rows: 3

## 4. Relevant Variables and Study Design

- Exposure: `bmi`
- Outcome: `hypertension`
- Confounders: `age`, `sex`
- Suggested additional confounders: `smoking`, `diabetes`
- Unavailable variables from question: None identified
- Inferred study design: `trial_or_longitudinal_like`
- Study design confidence: `low`
- Study design note: This workflow uses simple column-name heuristics; ask the user to confirm study design.

No warnings detected by v0.2 checks.


## 5. Missing Data Summary

| Variable | Missing Count | Missing Rate | Role |
|---|---:|---:|---|
| `death_date` | 290 | 96.7% |  |
| `bmi` | 70 | 23.3% | key variable |
| `hypertension` | 3 | 1.0% | key variable |

### Key-variable complete-case readiness

- Complete-case rate for mapped key variables: 75.7% across `bmi`, `hypertension`, `age`, `sex`
- Rows missing any mapped key variable: 73

### Row-level missingness burden

- Rows with any missing value: 296 (98.7%)
- Rows missing at least 30% of columns: 0 (0.0%)
- Overall missing-cell rate: 6.7%

### Missingness co-occurrence screening

- No co-occurring missingness pairs detected.

### Missingness mechanism screening caveat

This screening summarizes missingness evidence for human review and does not classify missingness as MCAR, MAR, or MNAR.

- Readiness flags: `key_variable_missingness_high`, `complete_case_rate_low`, `near_empty_columns_detected`


## 6. Biomedical Plausibility Warnings

These warnings indicate potential plausibility issues. They do not prove that records are incorrect and require human confirmation.

| Severity | Issue | Variable | Count | Description | Recommended Action | Example Rows |
|---|---|---|---:|---|---|---|
| critical | MED_DUPLICATE_PATIENT_ID | patient_id | 3 | Duplicate patient_id values were detected. | Confirm whether repeated IDs are duplicate records or longitudinal visits. | 29, 30, 31 |
| critical | MED_LOGIC_001 | sbp, dbp | 1 | Systolic blood pressure should not be lower than diastolic blood pressure. | Verify blood pressure entries. | 4 |
| critical | MED_LOGIC_002 | death_date, visit_date | 1 | Death date should not be earlier than visit date. | Verify visit and death dates. | 5 |
| critical | MED_LOGIC_003 | follow_up_days | 1 | Follow-up time should not be negative. | Verify follow-up duration and date-derived fields. | 6 |
| critical | MED_RANGE_AGE | age | 2 | Age should be between 0 and 120 years. | Verify age values and units. | 0, 1 |
| high | MED_RANGE_BMI | bmi | 2 | BMI is outside the broad adult plausibility range. | Verify height, weight, BMI calculation, and units. | 2, 3 |
| medium | MED_SEX_CODING_INCONSISTENCY | sex | 7 | Sex coding uses multiple representations that appear to map to the same concepts. | Standardize coding after confirming the intended values. |  |


## 7. Statistical Risk Warnings

| Severity | Issue | Variable | Count | Description | Recommended Action | Example Rows |
|---|---|---|---:|---|---|---|
| high | MISS_KEY_COMPLETE_CASE_LOW | bmi,hypertension,age,sex | 73 | Only 75.7% of rows are complete for the mapped exposure, outcome, and confounder variables. | Review the missingness pattern and confirm whether complete-case analysis is acceptable before modeling. Do not impute or drop rows automatically. | 40, 41, 42, 43, 44 |
| high | STAT_KEY_MISSING_BMI | bmi | 70 | Key variable `bmi` has 70 missing values (23.3%). | Assess missingness before complete-case analysis or modeling. |  |
| high | STAT_OUTCOME_IMBALANCE_HYPERTENSION | hypertension | 297 | Outcome `hypertension` is imbalanced: `No` is 92.9% of non-missing values. | Inspect event counts before logistic regression or classification. |  |
| medium | MISS_MECHANISM_REVIEW_NEEDED | dataset |  | Missingness evidence may be structured or analysis-threatening. | Confirm the data-collection process, missing-value codes, and planned handling with a qualified reviewer before analysis. |  |
| medium | MISS_NEAR_EMPTY_COLUMNS | death_date | 1 | 1 column is missing in at least 80% of rows. | Confirm whether these columns were collected and whether they belong in the planned analysis. |  |
| medium | STAT_EXTREME_OUTLIERS_BMI | bmi | 1 | Variable `bmi` has 1 extreme numeric outliers by a 3*IQR rule. | Inspect outliers and confirm units before modeling. | 3 |
| medium | STAT_NEAR_UNIQUE_EMAIL | email | 300 | Variable `email` is near-unique and may behave like an identifier. | Do not use identifier-like variables as predictors without a clear plan. |  |
| medium | STAT_NEAR_UNIQUE_PATIENT_ID | patient_id | 298 | Variable `patient_id` is near-unique and may behave like an identifier. | Do not use identifier-like variables as predictors without a clear plan. |  |
| medium | STAT_NEAR_UNIQUE_PATIENT_NAME | patient_name | 300 | Variable `patient_name` is near-unique and may behave like an identifier. | Do not use identifier-like variables as predictors without a clear plan. |  |


## 8. Privacy / PII Warnings

Do not upload identifiable patient data to external AI tools. Treat privacy warnings as blockers for external sharing until the data is de-identified or the field is removed, hashed, generalized, or otherwise handled according to the study policy.

| Severity | Issue | Variable | Count | Description | Recommended Action | Example Rows |
|---|---|---|---:|---|---|---|
| critical | PRIV_DIRECT_IDENTIFIER | patient_name |  | Potential direct identifier field detected. | Do not upload identifiable patient data to external AI tools. Remove, hash, or replace this field before analysis. |  |
| critical | PRIV_DIRECT_IDENTIFIER | email |  | Potential direct identifier field detected. | Do not upload identifiable patient data to external AI tools. Remove, hash, or replace this field before analysis. |  |


## 9. Analysis-readiness Notes

A binary-outcome association analysis may be considered after readiness issues are reviewed. The primary exposure is `bmi`, the outcome is `hypertension`, and the requested adjustment variables are `age`, `sex`. Do not proceed to modeling until these high-priority issues are reviewed: MED_RANGE_AGE on age; MED_RANGE_BMI on bmi; MED_LOGIC_001 on sbp, dbp; MED_LOGIC_002 on death_date, visit_date; MED_LOGIC_003 on follow_up_days. This workflow does not fit statistical models or report model estimates. Interpret future results as association unless the study design and analysis plan justify causal language.

## 10. Iterative Extraction Requests

These requests ask for metadata, column names, definitions, coding rules, units, and de-identification confirmation. Do not provide raw patient rows or direct identifier values.

| Priority | Request Type | Related Variables | Request | Safe Response |
|---|---|---|---|---|
| blocker | confirm_privacy_handling | `email`, `patient_name` | Please confirm that direct identifiers are removed, hashed, generalized, or handled under an approved privacy policy before external AI use. | Do not provide raw patient rows or direct identifier values. Do not provide names, phone numbers, emails, addresses, notes, screenshots, or full extracts. |
| high | confirm_study_design | None | Please confirm whether the data are cross-sectional, cohort, case-control, trial, repeated-measures, or another design. | Do not provide raw patient rows or direct identifier values. Provide protocol or design metadata only. |
| high | confirm_missingness_handling | `age`, `bmi`, `death_date`, `hypertension`, `sex` | Please confirm whether missing values mean not collected, not applicable, unknown, refused, or structurally missing. | Do not provide raw patient rows or direct identifier values. Provide coding rules and collection policy only; do not fill, impute, or paste values. |
| high | confirm_outcome_definition | `hypertension` | Please confirm the outcome definition and coding for `hypertension`, including which code represents the event. | Do not provide raw patient rows or direct identifier values. Provide the coding dictionary only. |
| high | confirm_repeated_measures | `patient_id` | Please confirm whether repeated patient IDs represent duplicate records, repeated visits, multiple measurements, or longitudinal follow-up. | Do not provide raw patient rows or direct identifier values. Describe the record structure without listing patient IDs. |
| high | confirm_time_window | `death_date`, `visit_date`, `follow_up_days` | Please confirm the index date, follow-up window, and outcome ascertainment period. | Do not provide raw patient rows or direct identifier values. Provide date-field definitions and window rules only. |
| medium | confirm_population | `age`, `bmi`, `death_date`, `follow_up_days`, `hypertension`, `sex`, `visit_date` | Please confirm the intended analysis population and any inclusion or exclusion criteria. | Do not provide raw patient rows or direct identifier values. Provide eligibility rules or aggregate counts only. |
| medium | provide_data_dictionary | `hypertension`, `sex` | Please provide a de-identified data dictionary for the key variables, including definitions, allowed codes, and units. | Do not provide raw patient rows or direct identifier values. Provide metadata excerpts only. |

## 11. Questions for Human Confirmation

- Please confirm `MED_RANGE_AGE` for `age`: Age should be between 0 and 120 years.
- Please confirm `MED_RANGE_BMI` for `bmi`: BMI is outside the broad adult plausibility range.
- Please confirm `MED_LOGIC_001` for `sbp, dbp`: Systolic blood pressure should not be lower than diastolic blood pressure.
- Please confirm `MED_LOGIC_002` for `death_date, visit_date`: Death date should not be earlier than visit date.
- Please confirm `MED_LOGIC_003` for `follow_up_days`: Follow-up time should not be negative.
- Please confirm `MED_DUPLICATE_PATIENT_ID` for `patient_id`: Duplicate patient_id values were detected.
- Please confirm `MISS_KEY_COMPLETE_CASE_LOW` for `bmi,hypertension,age,sex`: Only 75.7% of rows are complete for the mapped exposure, outcome, and confounder variables.
- Please confirm `PRIV_DIRECT_IDENTIFIER` for `patient_name`: Potential direct identifier field detected.
- Please confirm `PRIV_DIRECT_IDENTIFIER` for `email`: Potential direct identifier field detected.

## 12. Token-saving Summary

The dataset contains 300 records and 18 variables. The user question maps to exposure `bmi`, outcome `hypertension`, and confounders `age`, `sex`. Major issues include MED_RANGE_AGE (age); MED_RANGE_BMI (bmi); MED_LOGIC_001 (sbp, dbp); MED_LOGIC_002 (death_date, visit_date); MED_LOGIC_003 (follow_up_days); MED_DUPLICATE_PATIENT_ID (patient_id); STAT_KEY_MISSING_BMI (bmi); MISS_KEY_COMPLETE_CASE_LOW (bmi,hypertension,age,sex). This report is designed to let an AI assistant reason from compact full-dataset evidence rather than raw row samples.

## 13. Limitations and Safety Notes

- This report is not a clinical decision tool.
- This report does not diagnose disease.
- This report does not recommend treatment.
- This report does not verify real-world medical truth.
- This workflow does not fit statistical models or report model estimates.
- This workflow does not clean data or modify the source dataset.
- This workflow does not replace a statistician or clinical data manager.
- This workflow should not be used with identifiable patient data.
- Do not upload real patient data or direct identifiers to external AI systems.
- Medical plausibility warnings require human confirmation.
- Privacy warnings require review before external sharing.
- This workflow supports analysis-readiness review, not automatic causal inference.

Approximate source CSV tokens: 9236. Approximate report tokens: 3302. Compression ratio: 2.8:1. Method: character-count / 4 estimate; not exact tokenizer output.
