from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from pandas.api.types import is_numeric_dtype

from .missingness_readiness import check_missingness_readiness
from .schemas import make_warning


DEFAULT_RULES = Path(__file__).resolve().parents[1] / "rules" / "statistical_rules.yaml"


def load_statistical_rules(path: str | Path | None = None) -> dict[str, Any]:
    with Path(path or DEFAULT_RULES).open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _load_yaml(path: str | Path | None, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    return fallback if fallback is not None else load_statistical_rules(path)


def _looks_date_like(column: str, series: pd.Series) -> bool:
    if "date" not in column.lower() and column.lower() not in {"dob", "birth_date", "death_date"}:
        return False
    parsed = pd.to_datetime(series.dropna(), errors="coerce")
    return not parsed.empty and parsed.notna().mean() >= 0.80


def _flatten_relevant_vars(variable_roles: dict[str, Any] | None) -> list[str]:
    if not variable_roles:
        return []
    result: list[str] = []
    for key in ("exposure", "outcome", "confounders"):
        for value in variable_roles.get(key, []) or []:
            if value not in result:
                result.append(value)
    return result


def check_small_sample_size(df: pd.DataFrame, threshold: int = 100) -> list[dict[str, Any]]:
    if len(df) >= threshold:
        return []
    return [
        make_warning(
            "STAT_SMALL_SAMPLE",
            "statistical_risk",
            "high",
            "dataset",
            f"Dataset has {len(df)} rows, below the configured minimum of {threshold}.",
            "Use caution with regression or subgroup analysis.",
            count=int(len(df)),
            human_confirmation_required=False,
        )
    ]


def check_key_variable_missingness(
    df: pd.DataFrame,
    variable_roles: dict[str, Any],
    high_threshold: float = 0.20,
    critical_threshold: float = 0.40,
) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for variable in [var for var in _flatten_relevant_vars(variable_roles) if var in df.columns]:
        missing_count = int(df[variable].isna().sum())
        missing_rate = missing_count / max(len(df), 1)
        if missing_rate >= high_threshold:
            severity = "critical" if missing_rate >= critical_threshold else "high"
            warnings.append(
                make_warning(
                    f"STAT_KEY_MISSING_{variable.upper()}",
                    "statistical_risk",
                    severity,
                    variable,
                    f"Key variable `{variable}` has {missing_count} missing values ({missing_rate:.1%}).",
                    "Assess missingness before complete-case analysis or modeling.",
                    count=missing_count,
                    human_confirmation_required=False,
                )
            )
    return warnings


def check_outcome_imbalance(
    df: pd.DataFrame,
    outcome: str,
    threshold: float = 0.90,
    min_events: int = 10,
) -> list[dict[str, Any]]:
    if outcome not in df.columns:
        return []
    warnings: list[dict[str, Any]] = []
    counts = df[outcome].dropna().astype(str).value_counts()
    if counts.empty:
        return []
    largest_rate = counts.iloc[0] / counts.sum()
    if largest_rate >= threshold:
        warnings.append(
            make_warning(
                f"STAT_OUTCOME_IMBALANCE_{outcome.upper()}",
                "statistical_risk",
                "high",
                outcome,
                f"Outcome `{outcome}` is imbalanced: `{counts.index[0]}` is {largest_rate:.1%} of non-missing values.",
                "Inspect event counts before logistic regression or classification.",
                count=int(counts.sum()),
                human_confirmation_required=False,
            )
        )
    if len(counts) == 2 and counts.min() < min_events:
        warnings.append(
            make_warning(
                f"STAT_FEW_OUTCOME_EVENTS_{outcome.upper()}",
                "statistical_risk",
                "high",
                outcome,
                f"Outcome `{outcome}` has only {int(counts.min())} events in the smaller class.",
                "Avoid overfitted models and reduce predictors unless reviewed by a statistician.",
                count=int(counts.min()),
                human_confirmation_required=False,
            )
        )
    return warnings


def check_sparse_categories(df: pd.DataFrame, min_count: int = 5, max_levels: int = 50) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for column in df.columns:
        series = df[column]
        if is_numeric_dtype(series) or _looks_date_like(column, series):
            continue
        counts = series.dropna().astype(str).value_counts()
        if 1 < len(counts) <= max_levels:
            sparse_levels = counts[counts < min_count]
            if not sparse_levels.empty:
                warnings.append(
                    make_warning(
                        f"STAT_SPARSE_LEVELS_{column.upper()}",
                        "statistical_risk",
                        "medium",
                        column,
                        f"Variable `{column}` has {len(sparse_levels)} sparse categorical levels.",
                        "Combine levels, remove rare categories, or use exact methods when appropriate.",
                        count=int(len(sparse_levels)),
                        human_confirmation_required=False,
                    )
                )
    return warnings


def check_numeric_outliers(df: pd.DataFrame) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for column in df.columns:
        numeric = pd.to_numeric(df[column], errors="coerce")
        if numeric.notna().sum() < 20:
            continue
        q1 = numeric.quantile(0.25)
        q3 = numeric.quantile(0.75)
        iqr = q3 - q1
        if iqr <= 0:
            continue
        mask = (numeric < q1 - 3 * iqr) | (numeric > q3 + 3 * iqr)
        if mask.sum() > 0:
            warnings.append(
                make_warning(
                    f"STAT_EXTREME_OUTLIERS_{column.upper()}",
                    "statistical_risk",
                    "medium",
                    column,
                    f"Variable `{column}` has {int(mask.sum())} extreme numeric outliers by a 3*IQR rule.",
                    "Inspect outliers and confirm units before modeling.",
                    count=int(mask.sum()),
                    example_rows=[int(i) for i in mask[mask].index[:5].tolist()],
                    human_confirmation_required=True,
                )
            )
    return warnings


def check_near_unique_columns(df: pd.DataFrame, threshold: float = 0.95, high_unique_rate: float = 0.50, max_levels: int = 50) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for column in df.columns:
        series = df[column]
        non_null = series.dropna()
        if non_null.empty or _looks_date_like(column, series):
            continue
        unique_count = int(non_null.nunique())
        unique_rate = unique_count / max(len(non_null), 1)
        if unique_rate >= threshold and len(non_null) > 20:
            warnings.append(
                make_warning(
                    f"STAT_NEAR_UNIQUE_{column.upper()}",
                    "statistical_risk",
                    "medium",
                    column,
                    f"Variable `{column}` is near-unique and may behave like an identifier.",
                    "Do not use identifier-like variables as predictors without a clear plan.",
                    count=unique_count,
                    human_confirmation_required=False,
                )
            )
        elif (not is_numeric_dtype(series)) and (unique_count > max_levels or unique_rate > high_unique_rate):
            warnings.append(
                make_warning(
                    f"STAT_HIGH_CARDINALITY_{column.upper()}",
                    "statistical_risk",
                    "medium",
                    column,
                    f"Variable `{column}` has high cardinality ({unique_count} levels).",
                    "Review whether this is an identifier, free text, or unsuitable categorical predictor.",
                    count=unique_count,
                    human_confirmation_required=False,
                )
            )
    return warnings


def generate_model_readiness_warnings(df: pd.DataFrame, variable_roles: dict[str, Any]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    if variable_roles and (not variable_roles.get("exposure") or not variable_roles.get("outcome")):
        warnings.append(
            make_warning(
                "STAT_UNCLEAR_ANALYSIS_ROLE",
                "statistical_risk",
                "medium",
                "research_question",
                "The question-driven mapping did not identify both an exposure and an outcome.",
                "Ask the user to confirm the exposure, outcome, and adjustment variables before analysis.",
                human_confirmation_required=True,
            )
        )
    warnings.extend(_check_near_complete_separation(df, variable_roles))
    return warnings


def _check_near_complete_separation(df: pd.DataFrame, variable_roles: dict[str, Any] | None, min_level_count: int = 5) -> list[dict[str, Any]]:
    if not variable_roles:
        return []
    warnings: list[dict[str, Any]] = []
    outcome_vars = [var for var in variable_roles.get("outcome", []) if var in df.columns]
    predictors = [var for var in variable_roles.get("exposure", []) + variable_roles.get("confounders", []) if var in df.columns]
    for outcome in outcome_vars:
        outcome_values = df[outcome].dropna().astype(str)
        if outcome_values.nunique() != 2:
            continue
        for predictor in predictors:
            if is_numeric_dtype(df[predictor]):
                continue
            grouped = df[[predictor, outcome]].dropna().astype(str).groupby(predictor)[outcome]
            risky_levels = [level for level, values in grouped if len(values) >= min_level_count and values.nunique() == 1]
            if risky_levels:
                warnings.append(
                    make_warning(
                        f"STAT_SEPARATION_RISK_{predictor.upper()}",
                        "statistical_risk",
                        "medium",
                        predictor,
                        f"Predictor `{predictor}` has levels where outcome `{outcome}` takes only one class.",
                        "Check for complete or near-complete separation before logistic regression.",
                        count=len(risky_levels),
                        human_confirmation_required=False,
                    )
                )
    return warnings


def check_statistical_risks(
    df: pd.DataFrame,
    profile: dict[str, Any] | None = None,
    variable_roles: dict[str, Any] | None = None,
    relevant_vars: dict[str, Any] | None = None,
    rules_path: str | Path | None = None,
    rules: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    variable_roles = variable_roles or relevant_vars or {}
    loaded_rules = _load_yaml(rules_path, rules)
    sample_rules = loaded_rules.get("sample_size", {})
    missing_rules = loaded_rules.get("missingness", {})
    balance_rules = loaded_rules.get("outcome_balance", {})
    sparse_rules = loaded_rules.get("categorical_sparsity", {})
    card_rules = loaded_rules.get("cardinality", {})

    warnings: list[dict[str, Any]] = []
    warnings.extend(check_small_sample_size(df, threshold=sample_rules.get("min_total_n", 100)))
    warnings.extend(
        check_key_variable_missingness(
            df,
            variable_roles,
            high_threshold=missing_rules.get("high_missing_rate", 0.20),
            critical_threshold=missing_rules.get("critical_missing_rate", 0.40),
        )
    )
    warnings.extend(
        check_missingness_readiness(
            df,
            variable_roles=variable_roles,
            high_missing_rate=missing_rules.get("high_missing_rate", 0.20),
            critical_missing_rate=missing_rules.get("critical_missing_rate", 0.40),
        )
    )
    for outcome in [var for var in variable_roles.get("outcome", []) if var in df.columns]:
        warnings.extend(
            check_outcome_imbalance(
                df,
                outcome,
                threshold=balance_rules.get("severe_imbalance_threshold", 0.90),
                min_events=sample_rules.get("min_outcome_events", 10),
            )
        )
    warnings.extend(check_sparse_categories(df, min_count=sparse_rules.get("min_count_per_level", 5), max_levels=card_rules.get("max_categorical_levels", 50)))
    warnings.extend(check_numeric_outliers(df))
    warnings.extend(
        check_near_unique_columns(
            df,
            threshold=card_rules.get("near_unique_rate", 0.95),
            high_unique_rate=card_rules.get("high_unique_rate", 0.50),
            max_levels=card_rules.get("max_categorical_levels", 50),
        )
    )
    warnings.extend(generate_model_readiness_warnings(df, variable_roles))
    return warnings
