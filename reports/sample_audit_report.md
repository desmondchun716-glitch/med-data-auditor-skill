# AI-ready Biomedical Data Audit Report

## 1. User Question

Is BMI associated with hypertension after adjusting for age and sex?

## 2. Dataset Overview

- Rows: 300
- Columns: 18
- Variable type summary: 6 categorical, 2 date, 3 identifier-like, 7 numeric
- Potential ID columns: `patient_id`, `patient_name`, `email`
- Duplicate rows: 0
- Duplicate patient ID rows: 3

## 3. Relevant Variables and Study Design

- Exposure: `bmi`
- Outcome: `hypertension`
- Confounders: `age`, `sex`
- Suggested additional confounders: `smoking`, `diabetes`
- Unavailable variables from question: None identified
- Inferred study design: `trial_or_longitudinal_like`
- Study design confidence: `low`
- Study design note: v0.1 uses simple column-name heuristics; ask the user to confirm study design.

No warnings detected.


## 4. Missing Data Summary

| Variable | Missing Count | Missing Rate | Role |
|---|---:|---:|---|
| `death_date` | 290 | 96.7% |  |
| `bmi` | 70 | 23.3% | key variable |
| `hypertension` | 3 | 1.0% | key variable |


## 5. Biomedical Plausibility Warnings

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


## 6. Statistical Risk Warnings

| Severity | Issue | Variable | Count | Description | Recommended Action | Example Rows |
|---|---|---|---:|---|---|---|
| high | STAT_KEY_MISSING_BMI | bmi | 70 | Key variable `bmi` has 70 missing values (23.3%). | Assess missingness before complete-case analysis or modeling. |  |
| high | STAT_OUTCOME_IMBALANCE_HYPERTENSION | hypertension | 297 | Outcome `hypertension` is imbalanced: `No` is 92.9% of non-missing values. | Inspect event counts before logistic regression or classification. |  |
| medium | STAT_EXTREME_OUTLIERS_BMI | bmi | 1 | Variable `bmi` has 1 extreme numeric outliers by a 3*IQR rule. | Inspect outliers and confirm units before modeling. | 3 |
| medium | STAT_NEAR_UNIQUE_EMAIL | email | 300 | Variable `email` is near-unique and may behave like an identifier. | Do not use identifier-like variables as predictors without a clear plan. |  |
| medium | STAT_NEAR_UNIQUE_PATIENT_ID | patient_id | 298 | Variable `patient_id` is near-unique and may behave like an identifier. | Do not use identifier-like variables as predictors without a clear plan. |  |
| medium | STAT_NEAR_UNIQUE_PATIENT_NAME | patient_name | 300 | Variable `patient_name` is near-unique and may behave like an identifier. | Do not use identifier-like variables as predictors without a clear plan. |  |


## 7. Privacy / PII Warnings

Do not upload identifiable patient data to external AI tools.

| Severity | Issue | Variable | Count | Description | Recommended Action | Example Rows |
|---|---|---|---:|---|---|---|
| critical | PRIV_DIRECT_IDENTIFIER | patient_name |  | Potential direct identifier field detected. | Do not upload identifiable patient data to external AI tools. Remove, hash, or replace this field before analysis. |  |
| critical | PRIV_DIRECT_IDENTIFIER | email |  | Potential direct identifier field detected. | Do not upload identifiable patient data to external AI tools. Remove, hash, or replace this field before analysis. |  |


## 8. Analysis-readiness Notes

A binary-outcome association analysis may be considered after readiness issues are reviewed. The primary exposure is `bmi`, the outcome is `hypertension`, and the requested adjustment variables are `age`, `sex`. Do not proceed to modeling until these high-priority issues are reviewed: MED_RANGE_AGE on age; MED_RANGE_BMI on bmi; MED_LOGIC_001 on sbp, dbp; MED_LOGIC_002 on death_date, visit_date; MED_LOGIC_003 on follow_up_days. v0.1 does not fit statistical models or report model estimates. Interpret future results as association unless the study design and analysis plan justify causal language.

## 9. Questions for Human Confirmation

- Please confirm `MED_RANGE_AGE` for `age`: Age should be between 0 and 120 years.
- Please confirm `MED_RANGE_BMI` for `bmi`: BMI is outside the broad adult plausibility range.
- Please confirm `MED_LOGIC_001` for `sbp, dbp`: Systolic blood pressure should not be lower than diastolic blood pressure.
- Please confirm `MED_LOGIC_002` for `death_date, visit_date`: Death date should not be earlier than visit date.
- Please confirm `MED_LOGIC_003` for `follow_up_days`: Follow-up time should not be negative.
- Please confirm `MED_DUPLICATE_PATIENT_ID` for `patient_id`: Duplicate patient_id values were detected.
- Please confirm `PRIV_DIRECT_IDENTIFIER` for `patient_name`: Potential direct identifier field detected.
- Please confirm `PRIV_DIRECT_IDENTIFIER` for `email`: Potential direct identifier field detected.

## 10. Token-saving Summary

The dataset contains 300 records and 18 variables. The user question maps to exposure `bmi`, outcome `hypertension`, and confounders `age`, `sex`. Major issues include MED_RANGE_AGE (age); MED_RANGE_BMI (bmi); MED_LOGIC_001 (sbp, dbp); MED_LOGIC_002 (death_date, visit_date); MED_LOGIC_003 (follow_up_days); MED_DUPLICATE_PATIENT_ID (patient_id); STAT_KEY_MISSING_BMI (bmi); STAT_OUTCOME_IMBALANCE_HYPERTENSION (hypertension). This report is designed to let an AI assistant reason from compact full-dataset evidence rather than raw row samples.

## 11. Limitations and Safety Notes

- This report is not a clinical decision tool.
- This report does not verify real-world medical truth.
- This workflow does not replace a statistician or clinical data manager.
- This workflow should not be used with identifiable patient data.
- Medical plausibility warnings require human confirmation.
- v0.1 supports analysis-readiness review, not automatic causal inference.

Approximate source CSV tokens: 9236. Approximate report tokens: 1751. Compression ratio: 5.3:1.
