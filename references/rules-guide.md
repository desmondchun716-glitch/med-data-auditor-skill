# Rules Guide

Use this file when editing `rules/*.yaml` or adding deterministic checks.

## Medical Rule Defaults

`rules/medical_rules.yaml` supports numeric ranges and named logic rules.

```yaml
numeric_ranges:
  age:
    min: 0
    max: 120
    severity: critical

logic_rules:
  - id: MED_LOGIC_001
    name: sbp_less_than_dbp
    severity: critical
```

## Statistical Rule Defaults

`rules/statistical_rules.yaml` stores thresholds for analysis-readiness warnings.

```yaml
missingness:
  high_missing_rate: 0.20
  critical_missing_rate: 0.40

outcome_balance:
  severe_imbalance_threshold: 0.90
```

## Variable Dictionary Defaults

`rules/variable_dictionary.yaml` maps question terms to roles.

```yaml
bmi:
  synonyms:
    - bmi
    - body mass index
  default_role: exposure
```

## Authoring Rules

- Keep rules generic and conservative.
- Prefer warnings over automatic cleaning.
- Set `human_confirmation_required: true` for medical plausibility warnings.
- Do not add rules that imply clinical truth without study context.
- Add tests when a rule is meant to catch an injected sample-data issue.
