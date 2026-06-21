# Unit Warning Contract

## Purpose

WS4 adds deterministic warnings for possible biomedical unit or scale mismatches.

Core rule:

```text
WS4 warns about possible unit problems; it does not fix units.
```

Unit warnings are analysis-readiness evidence. They are not automatic data cleaning, clinical truth, or instructions to convert values.

## Runtime Behavior

`core/unit_warnings.py` exposes:

```python
check_unit_warnings(df) -> list[dict]
```

The function:

- reads the input DataFrame without mutating it
- uses conservative column-name and value-scale heuristics
- requires at least two numeric observations
- requires at least 70% of non-missing observations to match the suspicious scale
- emits existing `AuditWarning` dictionaries through `make_warning(...)`
- runs inside the existing medical plausibility warning pipeline

No new CLI flag or output mechanism is added. Unit warnings flow into the Markdown report, optional `audit_log.json`, and optional `flagged_records.csv` through the existing warning pipeline.

## AuditWarning Mapping

All unit warnings use:

```text
issue_type = medical_plausibility
severity = medium
human_confirmation_required = true
```

Issue IDs use the `UNIT_` prefix. Warning descriptions use cautious language such as:

- possible
- may indicate
- confirm before analysis
- do not convert automatically

## Supported Initial Unit-risk Categories

| Issue ID | Possible mismatch |
|---|---|
| `UNIT_BP_POSSIBLE_KPA` | Blood pressure kPa versus mmHg |
| `UNIT_TEMPERATURE_F_C_MISMATCH` | Temperature Fahrenheit versus Celsius |
| `UNIT_PERCENT_FRACTION_MISMATCH` | Percent versus fraction scale |
| `UNIT_HEIGHT_CM_AS_M` | Centimeters in a meter-labeled height field |
| `UNIT_HEIGHT_M_AS_CM` | Meters in a centimeter-labeled height field |
| `UNIT_WEIGHT_LB_AS_KG` | Pounds versus kilograms |
| `UNIT_GLUCOSE_MGDL_MMOLL_MISMATCH` | Glucose mg/dL versus mmol/L |
| `UNIT_CREATININE_MGDL_UMOL_MISMATCH` | Creatinine mg/dL versus umol/L |
| `UNIT_LIPID_MGDL_MMOLL_MISMATCH` | Lipid mg/dL versus mmol/L |

These checks intentionally require explicit column-name evidence when the unit family cannot be inferred safely. Generic unlabeled laboratory columns are not assigned a unit automatically.

## Allowed Evidence

Warnings may include:

- variable name
- affected-row count
- up to five row indexes
- possible unit-risk category
- confirmation-based recommended action

## Privacy Boundary

Warnings must not include:

- raw patient values
- full rows
- patient names
- email addresses
- phone numbers
- addresses
- direct identifier values
- clinical free text
- secrets or API keys

The warning text describes the scale pattern without repeating the source values.

## Forbidden Actions

WS4 must not:

- convert units
- overwrite or mutate source data
- create cleaned datasets
- impute values
- delete rows
- diagnose patients
- make clinical or regulatory claims
- add a new warning issue type
- call an external LLM
- implement an LLM Council runtime
- start WS5, WS6, or WS7

## Validation Rules

Tests must confirm:

- every warning matches the existing `AuditWarning` schema
- every warning uses a valid existing issue type
- the input DataFrame is unchanged
- expected synthetic unit-risk patterns produce the correct issue IDs
- normal synthetic values do not produce unit warnings
- warning text contains no raw source values
- unit warnings flow into the report, audit log, and flagged-records outputs
