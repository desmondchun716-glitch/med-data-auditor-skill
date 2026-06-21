from __future__ import annotations

from itertools import combinations
from typing import Any

import pandas as pd

from .schemas import make_warning


DEFAULT_LOW_KEY_COMPLETE_CASE_RATE = 0.80
DEFAULT_CRITICAL_KEY_COMPLETE_CASE_RATE = 0.60
DEFAULT_HIGH_ROW_MISSING_FRACTION = 0.30
DEFAULT_NEAR_EMPTY_COLUMN_RATE = 0.80
DEFAULT_COOCCURRENCE_PAIR_RATE = 0.20


def _safe_rate(count: int, denominator: int) -> float:
    return round(count / denominator, 4) if denominator else 0.0


def _example_positions(mask: pd.Series, limit: int = 5) -> list[int]:
    return [position for position, flagged in enumerate(mask.tolist()) if bool(flagged)][:limit]


def _flatten_key_variables(variable_roles: dict[str, Any] | None, columns: list[str]) -> list[str]:
    if not variable_roles:
        return []

    available = set(columns)
    key_variables: list[str] = []
    for role in ("exposure", "outcome", "confounders"):
        values = variable_roles.get(role, []) or []
        if isinstance(values, str):
            values = [values]
        for value in values:
            if isinstance(value, str) and value in available and value not in key_variables:
                key_variables.append(value)
    return key_variables


def build_missingness_readiness_metrics(
    df: pd.DataFrame,
    variable_roles: dict[str, Any] | None = None,
    high_missing_rate: float = 0.20,
    critical_missing_rate: float = 0.40,
    low_key_complete_case_rate: float = DEFAULT_LOW_KEY_COMPLETE_CASE_RATE,
    critical_key_complete_case_rate: float = DEFAULT_CRITICAL_KEY_COMPLETE_CASE_RATE,
    high_row_missing_fraction: float = DEFAULT_HIGH_ROW_MISSING_FRACTION,
    near_empty_column_rate: float = DEFAULT_NEAR_EMPTY_COLUMN_RATE,
    cooccurrence_pair_rate: float = DEFAULT_COOCCURRENCE_PAIR_RATE,
) -> dict[str, Any]:
    """Build deterministic, privacy-safe missingness evidence without modifying *df*."""
    total_rows = int(len(df))
    total_columns = int(len(df.columns))
    total_cells = total_rows * total_columns

    missing_mask = df.isna()
    column_missing_counts = missing_mask.sum(axis=0).astype(int)
    column_missing_rates = column_missing_counts / max(total_rows, 1)
    row_missing_counts = missing_mask.sum(axis=1).astype(int)

    columns_with_any_missing = [
        str(column) for column in df.columns if int(column_missing_counts[column]) > 0
    ]
    columns_with_high_missing = [
        str(column) for column in df.columns if float(column_missing_rates[column]) >= high_missing_rate
    ]
    columns_with_critical_missing = [
        str(column) for column in df.columns if float(column_missing_rates[column]) >= critical_missing_rate
    ]
    near_empty_columns = [
        str(column) for column in df.columns if float(column_missing_rates[column]) >= near_empty_column_rate
    ]

    top_missing_columns = sorted(
        [
            {
                "column": str(column),
                "missing_count": int(column_missing_counts[column]),
                "missing_rate": round(float(column_missing_rates[column]), 4),
            }
            for column in df.columns
            if int(column_missing_counts[column]) > 0
        ],
        key=lambda item: (-item["missing_count"], item["column"]),
    )[:15]

    rows_with_any_missing_mask = row_missing_counts > 0
    high_row_missing_threshold = max(1, int(total_columns * high_row_missing_fraction + 0.999999))
    high_row_missing_mask = row_missing_counts >= high_row_missing_threshold

    key_variables = _flatten_key_variables(variable_roles, [str(column) for column in df.columns])
    if key_variables:
        key_missing_mask = missing_mask[key_variables].any(axis=1)
        complete_case_count_for_key_variables = int((~key_missing_mask).sum())
        rows_missing_any_key_variable = int(key_missing_mask.sum())
        key_variables_with_missingness = [
            variable for variable in key_variables if int(column_missing_counts[variable]) > 0
        ]
    else:
        key_missing_mask = pd.Series(False, index=df.index)
        complete_case_count_for_key_variables = None
        rows_missing_any_key_variable = None
        key_variables_with_missingness = []

    missing_columns = [
        column
        for column in df.columns
        if int(column_missing_counts[column]) > 0
        and float(column_missing_rates[column]) < near_empty_column_rate
    ]
    cooccurrence_pairs: list[dict[str, Any]] = []
    for variable_a, variable_b in combinations(missing_columns, 2):
        joint_missing_count = int((missing_mask[variable_a] & missing_mask[variable_b]).sum())
        if joint_missing_count == 0:
            continue
        cooccurrence_pairs.append(
            {
                "variable_a": str(variable_a),
                "variable_b": str(variable_b),
                "joint_missing_count": joint_missing_count,
                "joint_missing_rate": _safe_rate(joint_missing_count, total_rows),
            }
        )
    cooccurrence_pairs.sort(
        key=lambda item: (
            -item["joint_missing_count"],
            item["variable_a"],
            item["variable_b"],
        )
    )
    top_cooccurrence_pairs = cooccurrence_pairs[:10]
    material_cooccurrence_pairs = [
        item for item in top_cooccurrence_pairs if item["joint_missing_rate"] >= cooccurrence_pair_rate
    ]

    total_missing_cells = int(row_missing_counts.sum())
    complete_rows_all_columns = int((row_missing_counts == 0).sum())
    high_row_missing_count = int(high_row_missing_mask.sum())
    complete_case_rate = (
        _safe_rate(complete_case_count_for_key_variables, total_rows)
        if complete_case_count_for_key_variables is not None and total_rows
        else None
    )

    mechanism_screening_indicators = {
        "key_variable_missingness_high": bool(
            key_variables
            and any(float(column_missing_rates[variable]) >= high_missing_rate for variable in key_variables)
        ),
        "complete_case_rate_low": bool(
            complete_case_rate is not None and complete_case_rate < low_key_complete_case_rate
        ),
        "row_missingness_burden_high": bool(high_row_missing_count > 0),
        "cooccurring_missingness_detected": bool(material_cooccurrence_pairs),
        "near_empty_columns_detected": bool(near_empty_columns),
    }
    readiness_flags = [
        name for name, detected in mechanism_screening_indicators.items() if detected
    ]

    return {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "columns_with_any_missing": columns_with_any_missing,
        "columns_with_high_missing": columns_with_high_missing,
        "columns_with_critical_missing": columns_with_critical_missing,
        "near_empty_columns": near_empty_columns,
        "rows_with_any_missing": int(rows_with_any_missing_mask.sum()),
        "rows_with_any_missing_rate": _safe_rate(int(rows_with_any_missing_mask.sum()), total_rows),
        "complete_rows_all_columns": complete_rows_all_columns,
        "complete_rows_all_columns_rate": _safe_rate(complete_rows_all_columns, total_rows),
        "max_missing_cells_in_row": int(row_missing_counts.max()) if total_rows else 0,
        "mean_missing_cells_per_row": round(float(row_missing_counts.mean()), 4) if total_rows else 0.0,
        "overall_missing_cell_rate": _safe_rate(total_missing_cells, total_cells),
        "rows_with_high_missing_burden": high_row_missing_count,
        "rows_with_high_missing_burden_rate": _safe_rate(high_row_missing_count, total_rows),
        "high_row_missing_fraction": high_row_missing_fraction,
        "key_variables": key_variables,
        "complete_case_count_for_key_variables": complete_case_count_for_key_variables,
        "complete_case_rate_for_key_variables": complete_case_rate,
        "rows_missing_any_key_variable": rows_missing_any_key_variable,
        "rows_missing_any_key_variable_rate": (
            _safe_rate(rows_missing_any_key_variable, total_rows)
            if rows_missing_any_key_variable is not None and total_rows
            else None
        ),
        "key_variables_with_missingness": key_variables_with_missingness,
        "top_missing_columns": top_missing_columns,
        "top_missingness_cooccurrence_pairs": top_cooccurrence_pairs,
        "mechanism_screening_indicators": mechanism_screening_indicators,
        "readiness_flags": readiness_flags,
        "mechanism_screening_caveat": (
            "This screening summarizes missingness evidence for human review and does not "
            "classify missingness as MCAR, MAR, or MNAR."
        ),
        "thresholds": {
            "high_missing_rate": high_missing_rate,
            "critical_missing_rate": critical_missing_rate,
            "low_key_complete_case_rate": low_key_complete_case_rate,
            "critical_key_complete_case_rate": critical_key_complete_case_rate,
            "high_row_missing_fraction": high_row_missing_fraction,
            "near_empty_column_rate": near_empty_column_rate,
            "cooccurrence_pair_rate": cooccurrence_pair_rate,
        },
    }


def check_missingness_readiness(
    df: pd.DataFrame,
    variable_roles: dict[str, Any] | None = None,
    high_missing_rate: float = 0.20,
    critical_missing_rate: float = 0.40,
) -> list[dict[str, Any]]:
    metrics = build_missingness_readiness_metrics(
        df,
        variable_roles=variable_roles,
        high_missing_rate=high_missing_rate,
        critical_missing_rate=critical_missing_rate,
    )
    thresholds = metrics["thresholds"]
    warnings: list[dict[str, Any]] = []

    overall_rate = metrics["overall_missing_cell_rate"]
    if overall_rate >= high_missing_rate:
        severity = "high" if overall_rate >= critical_missing_rate else "medium"
        warnings.append(
            make_warning(
                "MISS_OVERALL_CELL_RATE_HIGH",
                "data_quality",
                severity,
                "dataset",
                f"Missing cells account for {overall_rate:.1%} of the dataset.",
                "Review collection and missing-value coding before selecting an analysis population.",
                count=int(df.isna().sum().sum()),
                human_confirmation_required=True,
            )
        )

    high_burden_count = metrics["rows_with_high_missing_burden"]
    if high_burden_count > 0:
        warnings.append(
            make_warning(
                "MISS_ROW_BURDEN_HIGH",
                "data_quality",
                "medium",
                "dataset",
                (
                    f"{high_burden_count} rows are missing at least "
                    f"{thresholds['high_row_missing_fraction']:.0%} of columns."
                ),
                "Review whether row-level missingness is clustered before complete-case analysis.",
                count=high_burden_count,
                example_rows=_example_positions(
                    df.isna().sum(axis=1)
                    >= max(
                        1,
                        int(
                            len(df.columns)
                            * thresholds["high_row_missing_fraction"]
                            + 0.999999
                        ),
                    )
                ),
                human_confirmation_required=True,
            )
        )

    near_empty_columns = metrics["near_empty_columns"]
    if near_empty_columns:
        key_columns = set(metrics["key_variables"])
        severity = "high" if key_columns.intersection(near_empty_columns) else "medium"
        column_word = "column is" if len(near_empty_columns) == 1 else "columns are"
        warnings.append(
            make_warning(
                "MISS_NEAR_EMPTY_COLUMNS",
                "data_quality",
                severity,
                ",".join(near_empty_columns),
                (
                    f"{len(near_empty_columns)} {column_word} missing in at least "
                    f"{thresholds['near_empty_column_rate']:.0%} of rows."
                ),
                "Confirm whether these columns were collected and whether they belong in the planned analysis.",
                count=len(near_empty_columns),
                human_confirmation_required=True,
            )
        )

    complete_case_rate = metrics["complete_case_rate_for_key_variables"]
    if complete_case_rate is not None and complete_case_rate < thresholds["low_key_complete_case_rate"]:
        severity = (
            "critical"
            if complete_case_rate < thresholds["critical_key_complete_case_rate"]
            else "high"
        )
        warnings.append(
            make_warning(
                "MISS_KEY_COMPLETE_CASE_LOW",
                "statistical_risk",
                severity,
                ",".join(metrics["key_variables"]),
                (
                    f"Only {complete_case_rate:.1%} of rows are complete for the mapped "
                    "exposure, outcome, and confounder variables."
                ),
                (
                    "Review the missingness pattern and confirm whether complete-case analysis "
                    "is acceptable before modeling. Do not impute or drop rows automatically."
                ),
                count=int(metrics["rows_missing_any_key_variable"]),
                example_rows=_example_positions(
                    df[metrics["key_variables"]].isna().any(axis=1)
                ),
                human_confirmation_required=True,
            )
        )

    material_pairs = [
        pair
        for pair in metrics["top_missingness_cooccurrence_pairs"]
        if pair["joint_missing_rate"] >= thresholds["cooccurrence_pair_rate"]
    ]
    if material_pairs:
        top_pair = material_pairs[0]
        pair_name = f"{top_pair['variable_a']},{top_pair['variable_b']}"
        pair_mask = df[top_pair["variable_a"]].isna() & df[top_pair["variable_b"]].isna()
        pair_word = "variable pair is" if len(material_pairs) == 1 else "variable pairs are"
        warnings.append(
            make_warning(
                "MISS_COOCCURRING_BLOCK",
                "statistical_risk",
                "medium",
                pair_name,
                (
                    f"{len(material_pairs)} {pair_word} jointly missing in at least "
                    f"{thresholds['cooccurrence_pair_rate']:.0%} of rows."
                ),
                "Review collection workflows and missing-value codes because missingness may be structured.",
                count=int(top_pair["joint_missing_count"]),
                example_rows=_example_positions(pair_mask),
                human_confirmation_required=True,
            )
        )

    indicators = metrics["mechanism_screening_indicators"]
    if indicators["cooccurring_missingness_detected"] or indicators["complete_case_rate_low"]:
        warnings.append(
            make_warning(
                "MISS_MECHANISM_REVIEW_NEEDED",
                "statistical_risk",
                "medium",
                "dataset",
                "Missingness evidence may be structured or analysis-threatening.",
                (
                    "Confirm the data-collection process, missing-value codes, and planned handling "
                    "with a qualified reviewer before analysis."
                ),
                human_confirmation_required=True,
            )
        )

    return warnings
