from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from pandas.api.types import is_numeric_dtype


DEFAULT_RULES = Path(__file__).resolve().parents[1] / "rules" / "statistical_rules.yaml"


def _looks_date_like(column: str, series: pd.Series) -> bool:
    if "date" not in column.lower() and column.lower() not in {"dob", "birth_date", "death_date"}:
        return False
    parsed = pd.to_datetime(series.dropna(), errors="coerce")
    return not parsed.empty and parsed.notna().mean() >= 0.80


def _load_yaml(path: str | Path | None, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    if fallback is not None:
        return fallback
    with Path(path or DEFAULT_RULES).open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _warning(
    issue_id: str,
    severity: str,
    variable: str,
    description: str,
    recommended_action: str,
    count: int | None = None,
    example_rows: list[int] | None = None,
    human_confirmation_required: bool = False,
) -> dict[str, Any]:
    return {
        "issue_id": issue_id,
        "issue_type": "statistical_risk",
        "severity": severity,
        "variable": variable,
        "count": count,
        "example_rows": example_rows or [],
        "description": description,
        "recommended_action": recommended_action,
        "human_confirmation_required": human_confirmation_required,
    }


def _flatten_relevant_vars(relevant_vars: dict[str, Any] | None) -> list[str]:
    if not relevant_vars:
        return []
    result: list[str] = []
    for key in ("exposure", "outcome", "confounders"):
        for value in relevant_vars.get(key, []) or []:
            if value not in result:
                result.append(value)
    return result


def check_statistical_risks(
    df: pd.DataFrame,
    relevant_vars: dict[str, Any] | None = None,
    rules_path: str | Path | None = None,
    rules: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    loaded_rules = _load_yaml(rules_path, rules)
    warnings: list[dict[str, Any]] = []

    n_rows = len(df)
    key_vars = [var for var in _flatten_relevant_vars(relevant_vars) if var in df.columns]
    outcome_vars = [var for var in (relevant_vars or {}).get("outcome", []) if var in df.columns]

    min_total_n = loaded_rules.get("sample_size", {}).get("min_total_n", 100)
    if n_rows < min_total_n:
        warnings.append(
            _warning(
                "STAT_SMALL_SAMPLE",
                "high",
                "dataset",
                f"Dataset has {n_rows} rows, below the configured minimum of {min_total_n}.",
                "Use caution with regression or subgroup analysis.",
                count=n_rows,
            )
        )

    high_missing = loaded_rules.get("missingness", {}).get("high_missing_rate", 0.20)
    critical_missing = loaded_rules.get("missingness", {}).get("critical_missing_rate", 0.40)
    for variable in key_vars:
        missing_count = int(df[variable].isna().sum())
        missing_rate = missing_count / max(n_rows, 1)
        if missing_rate >= high_missing:
            severity = "critical" if missing_rate >= critical_missing else "high"
            warnings.append(
                _warning(
                    f"STAT_KEY_MISSING_{variable.upper()}",
                    severity,
                    variable,
                    f"Key variable `{variable}` has {missing_count} missing values ({missing_rate:.1%}).",
                    "Assess missingness before complete-case analysis or modeling.",
                    count=missing_count,
                )
            )

    imbalance_threshold = loaded_rules.get("outcome_balance", {}).get("severe_imbalance_threshold", 0.90)
    min_events = loaded_rules.get("sample_size", {}).get("min_outcome_events", 10)
    for outcome in outcome_vars:
        counts = df[outcome].dropna().astype(str).value_counts()
        if counts.empty:
            continue
        largest_rate = counts.iloc[0] / counts.sum()
        if largest_rate >= imbalance_threshold:
            warnings.append(
                _warning(
                    f"STAT_OUTCOME_IMBALANCE_{outcome.upper()}",
                    "high",
                    outcome,
                    f"Outcome `{outcome}` is imbalanced: `{counts.index[0]}` is {largest_rate:.1%} of non-missing values.",
                    "Inspect event counts before logistic regression or classification.",
                    count=int(counts.sum()),
                )
            )
        if len(counts) == 2 and counts.min() < min_events:
            warnings.append(
                _warning(
                    f"STAT_FEW_OUTCOME_EVENTS_{outcome.upper()}",
                    "high",
                    outcome,
                    f"Outcome `{outcome}` has only {int(counts.min())} events in the smaller class.",
                    "Avoid overfitted models and reduce predictors unless reviewed by a statistician.",
                    count=int(counts.min()),
                )
            )

    sparse_min = loaded_rules.get("categorical_sparsity", {}).get("min_count_per_level", 5)
    max_levels = loaded_rules.get("cardinality", {}).get("max_categorical_levels", 50)
    high_unique_rate = loaded_rules.get("cardinality", {}).get("high_unique_rate", 0.50)
    near_unique_rate = loaded_rules.get("cardinality", {}).get("near_unique_rate", 0.95)

    for column in df.columns:
        series = df[column]
        date_like = _looks_date_like(column, series)
        missing_rate = series.isna().mean()
        if missing_rate == 1:
            warnings.append(
                _warning(
                    f"STAT_ALL_EMPTY_{column.upper()}",
                    "high",
                    column,
                    f"Variable `{column}` is completely empty.",
                    "Remove or recover the variable before analysis.",
                    count=n_rows,
                )
            )
            continue

        non_null = series.dropna()
        unique_count = int(non_null.nunique())
        unique_rate = unique_count / max(len(non_null), 1)

        if unique_rate >= near_unique_rate and len(non_null) > 20 and not date_like:
            warnings.append(
                _warning(
                    f"STAT_NEAR_UNIQUE_{column.upper()}",
                    "medium",
                    column,
                    f"Variable `{column}` is near-unique and may behave like an identifier.",
                    "Do not use identifier-like variables as predictors without a clear plan.",
                    count=unique_count,
                )
            )

        if not is_numeric_dtype(series) and not date_like:
            counts = non_null.astype(str).value_counts()
            if 1 < len(counts) <= max_levels:
                sparse_levels = counts[counts < sparse_min]
                if not sparse_levels.empty:
                    warnings.append(
                        _warning(
                            f"STAT_SPARSE_LEVELS_{column.upper()}",
                            "medium",
                            column,
                            f"Variable `{column}` has {len(sparse_levels)} sparse categorical levels.",
                            "Combine levels, remove rare categories, or use exact methods when appropriate.",
                            count=int(len(sparse_levels)),
                        )
                    )
            elif len(counts) > max_levels or unique_rate > high_unique_rate:
                warnings.append(
                    _warning(
                        f"STAT_HIGH_CARDINALITY_{column.upper()}",
                        "medium",
                        column,
                        f"Variable `{column}` has high cardinality ({unique_count} levels).",
                        "Review whether this is an identifier, free text, or unsuitable categorical predictor.",
                        count=unique_count,
                    )
                )

        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().sum() >= 20:
            q1 = numeric.quantile(0.25)
            q3 = numeric.quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                mask = (numeric < q1 - 3 * iqr) | (numeric > q3 + 3 * iqr)
                if mask.sum() > 0:
                    warnings.append(
                        _warning(
                            f"STAT_EXTREME_OUTLIERS_{column.upper()}",
                            "medium",
                            column,
                            f"Variable `{column}` has {int(mask.sum())} extreme numeric outliers by a 3*IQR rule.",
                            "Inspect outliers and confirm units before modeling.",
                            count=int(mask.sum()),
                            example_rows=[int(i) for i in mask[mask].index[:5].tolist()],
                            human_confirmation_required=True,
                        )
                    )

    warnings.extend(_check_near_complete_separation(df, relevant_vars, sparse_min))

    if relevant_vars and (not relevant_vars.get("exposure") or not relevant_vars.get("outcome")):
        warnings.append(
            _warning(
                "STAT_UNCLEAR_ANALYSIS_ROLE",
                "medium",
                "research_question",
                "The question-driven mapping did not identify both an exposure and an outcome.",
                "Ask the user to confirm the exposure, outcome, and adjustment variables before analysis.",
                human_confirmation_required=True,
            )
        )

    return warnings


def _check_near_complete_separation(
    df: pd.DataFrame,
    relevant_vars: dict[str, Any] | None,
    min_level_count: int,
) -> list[dict[str, Any]]:
    if not relevant_vars:
        return []
    warnings: list[dict[str, Any]] = []
    outcome_vars = [var for var in relevant_vars.get("outcome", []) if var in df.columns]
    predictors = [var for var in relevant_vars.get("exposure", []) + relevant_vars.get("confounders", []) if var in df.columns]

    for outcome in outcome_vars:
        outcome_values = df[outcome].dropna().astype(str)
        if outcome_values.nunique() != 2:
            continue
        for predictor in predictors:
            if is_numeric_dtype(df[predictor]):
                continue
            grouped = df[[predictor, outcome]].dropna().astype(str).groupby(predictor)[outcome]
            risky_levels = []
            for level, values in grouped:
                if len(values) >= min_level_count and values.nunique() == 1:
                    risky_levels.append(level)
            if risky_levels:
                warnings.append(
                    _warning(
                        f"STAT_SEPARATION_RISK_{predictor.upper()}",
                        "medium",
                        predictor,
                        f"Predictor `{predictor}` has levels where outcome `{outcome}` takes only one class.",
                        "Check for complete or near-complete separation before logistic regression.",
                        count=len(risky_levels),
                    )
                )
    return warnings
