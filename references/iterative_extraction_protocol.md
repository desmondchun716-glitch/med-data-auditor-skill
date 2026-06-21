# Iterative Extraction Protocol

## Purpose

WS6 converts audit evidence into a deterministic, prioritized list of safe next-step questions.

The protocol tells a human what metadata, definitions, confirmations, or de-identified additional variables are needed before analysis readiness can be reassessed.

Iterative extraction requests are questions for human confirmation, not automated data collection.

## Scope

WS6 may request:

- column names
- data dictionary excerpts
- unit definitions
- coding dictionaries
- missing-value code policies
- study design metadata
- analysis population definitions
- time-window definitions
- de-identification policy confirmation
- confirmation that additional de-identified variables exist

WS6 must:

- remain deterministic
- use existing profile, variable-role, study-design, and warning evidence
- group related warnings into one request when practical
- rank requests by priority
- emit no more than 10 requests by default
- require human confirmation for every request
- include safe-response guidance for every request

## Non-goals

WS6 does not:

- extract data
- inspect or request raw patient rows
- request direct identifier values
- call external services or LLM APIs
- add connectors or email automation
- modify the source dataset
- clean or impute data
- convert units
- fit statistical models
- add a new CLI flag
- add a new output file
- add a new audit-log top-level key
- add requests to `flagged_records.csv`

## Request Schema

Each request contains exactly:

```text
request_id
priority
request_type
trigger_source
related_variables
related_issue_ids
question
why_needed
expected_response
safe_response_guidance
human_confirmation_required
```

`request_id` is deterministic and uses:

```text
EXT_<CATEGORY>_<NNN>
```

Examples:

```text
EXT_PRIVACY_001
EXT_VAR_ROLE_001
EXT_UNIT_001
```

Allowed priorities:

```text
blocker
high
medium
low
```

Allowed request types:

```text
confirm_variable_role
provide_data_dictionary
confirm_units
confirm_missingness_handling
confirm_study_design
provide_additional_variables
confirm_privacy_handling
confirm_outcome_definition
confirm_population
confirm_time_window
confirm_repeated_measures
```

Allowed trigger sources:

```text
user_question
variable_mapping
study_design
medical_warning
unit_warning
statistical_warning
missingness_readiness
privacy_warning
profile
```

Allowed expected responses:

```text
yes_no
short_text
column_name_list
data_dictionary_excerpt
unit_definition
coding_dictionary
study_design_metadata
missingness_code_policy
deidentification_policy
analysis_population_definition
time_window_definition
```

`human_confirmation_required` is always `true`.

## Trigger Policy

| Evidence | Request | Default priority |
|---|---|---|
| Missing exposure or outcome mapping | `confirm_variable_role` | blocker |
| Variables mentioned in the question but absent from the CSV | `provide_additional_variables` | high |
| `UNIT_` warning | grouped `confirm_units` | high |
| `MISS_` warning or missingness readiness flag | grouped `confirm_missingness_handling` | high or medium |
| Privacy warning or direct identifier column | grouped `confirm_privacy_handling` | blocker |
| Low-confidence or warning-supported study design | `confirm_study_design` | high |
| Categorical outcome or outcome-risk warning | `confirm_outcome_definition` | high |
| Duplicate patient IDs or repeated-ID evidence | `confirm_repeated_measures` | high |
| Missingness, time, or design ambiguity affecting eligibility | `confirm_population` | medium |
| Date, follow-up, longitudinal, or time-warning evidence | `confirm_time_window` | high or medium |
| Uncertain roles, unit warnings, or coding warnings | grouped `provide_data_dictionary` | medium |

## Prioritization And Deduplication

Priority order:

```text
blocker
high
medium
low
```

Within a priority, use:

```text
privacy
missing exposure/outcome
study design
unit confirmation
missingness handling
outcome coding
additional variables
repeated measures
population/time window
data dictionary
```

Group warning families:

- many `UNIT_` warnings become one unit request
- many `MISS_` warnings become one missingness request
- many privacy warnings become one privacy request

Do not emit one request per warning when a grouped request is sufficient.

## Privacy Boundary

Every request includes:

```text
Do not provide raw patient rows or direct identifier values.
```

Requests must not ask for:

- names
- phone numbers
- email values
- addresses
- ID numbers
- full clinical notes
- identifiable screenshots
- patient-level extracts
- API keys or secrets

Column names may be listed because they are metadata. Raw warning descriptions, recommended actions, category values, and cell values must not be copied into extraction requests.

## Report Behavior

The Markdown report includes:

```text
## 10. Iterative Extraction Requests
```

The section renders at most 10 requests in a compact table:

```text
| Priority | Request Type | Related Variables | Request | Safe Response |
```

The existing human-confirmation, token-summary, and limitation sections follow it.

## Audit Log Behavior

Requests are stored under the existing analysis context:

```json
{
  "analysis_context": {
    "variable_roles": {},
    "study_design": {},
    "extraction_requests": []
  }
}
```

No new top-level audit-log key is added.

Each request must pass `validate_extraction_request_schema(...)`, and the full list must pass `validate_extraction_requests_schema(...)`.

## Flagged Records Behavior

`flagged_records.csv` remains a row-reference issue index derived from warnings with `example_rows`.

Extraction requests are not warnings and do not change the flagged-record schema.

## Validation Rules

Validation must confirm:

- exact request fields
- allowed enum values
- deterministic request IDs
- stable priority ordering
- grouped unit, missingness, and privacy requests
- no more than the configured request limit
- no raw-value copying
- safe-response guidance on every request
- report section and caveat rendering
- storage under `audit_log["analysis_context"]["extraction_requests"]`
- unchanged audit-log top-level keys
- unchanged flagged-record fields
- no source-data mutation
