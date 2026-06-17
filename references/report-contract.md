# Report Contract

Use this file when editing `scripts/07_generate_report.py` or changing required report sections.

## Required Sections

1. User Question
2. Dataset Overview
3. Relevant Variables
4. Missing Data Summary
5. Medical Plausibility Warnings
6. Statistical Risk Warnings
7. Privacy / Identifier Warnings
8. Analysis-readiness Notes
9. Questions for Human Confirmation
10. Token-saving Summary
11. Limitations

## Warning Schema

Each warning should preserve these fields when practical:

```json
{
  "issue_id": "MED_001",
  "issue_type": "medical_plausibility",
  "severity": "critical",
  "variable": "sbp",
  "count": 14,
  "example_rows": [12, 88, 291],
  "description": "SBP is lower than DBP.",
  "recommended_action": "Verify blood pressure entries.",
  "human_confirmation_required": true
}
```

## Quality Rules

- Prefer concrete evidence over vague wording.
- Include counts, rates, variables, and example rows when available.
- Use association language unless a study design and analysis justify stronger wording.
- State that medical plausibility warnings require human confirmation.
- State that the report is not a clinical decision tool.

## Bad And Good Report Language

Bad:

```text
Some variables have missing values.
```

Good:

```text
BMI has 70 missing values (23.3%) and is the exposure variable in the user question. This may bias the association analysis if missingness is related to age, sex, or hypertension.
```

Bad:

```text
The dataset proves BMI causes hypertension.
```

Good:

```text
The dataset may support association analysis after missingness, duplicates, and medical plausibility warnings are reviewed; v0.1 does not run or report a fitted model.
```
