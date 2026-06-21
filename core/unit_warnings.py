from __future__ import annotations

import re
from typing import Any

import pandas as pd

from .schemas import make_warning


_MIN_OBSERVATIONS = 2
_MAJORITY_THRESHOLD = 0.7


def _normalize_column(column: object) -> str:
    text = str(column).strip().lower().replace("μ", "u").replace("µ", "u")
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _example_rows(mask: pd.Series, limit: int = 5) -> list[int]:
    return [int(index) for index in mask[mask].index[:limit].tolist()]


def _numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce")


def _is_majority(values: pd.Series, mask: pd.Series) -> bool:
    observed = int(values.notna().sum())
    matched = int(mask.sum())
    return observed >= _MIN_OBSERVATIONS and matched >= _MIN_OBSERVATIONS and matched / observed >= _MAJORITY_THRESHOLD


def _has_any(text: str, markers: set[str]) -> bool:
    return any(marker in text for marker in markers)


def _unit_warning(
    *,
    issue_id: str,
    variable: str,
    mask: pd.Series,
    description: str,
) -> dict[str, Any]:
    return make_warning(
        issue_id=issue_id,
        issue_type="medical_plausibility",
        severity="medium",
        variable=variable,
        description=description,
        recommended_action=(
            "Confirm the intended unit and source documentation before analysis. "
            "Do not convert automatically without human confirmation."
        ),
        count=int(mask.sum()),
        example_rows=_example_rows(mask),
        human_confirmation_required=True,
    )


def _blood_pressure_warnings(df: pd.DataFrame) -> list[dict[str, Any]]:
    normalized = {column: _normalize_column(column) for column in df.columns}
    sbp_columns = [
        column
        for column, name in normalized.items()
        if name in {"sbp", "systolic_bp", "systolic_blood_pressure"}
    ]
    dbp_columns = [
        column
        for column, name in normalized.items()
        if name in {"dbp", "diastolic_bp", "diastolic_blood_pressure"}
    ]
    if not sbp_columns and not dbp_columns:
        return []

    columns = [*sbp_columns[:1], *dbp_columns[:1]]
    masks: list[pd.Series] = []
    values_for_threshold: list[pd.Series] = []
    if sbp_columns:
        sbp = _numeric_series(df, sbp_columns[0])
        masks.append(sbp.between(8, 35, inclusive="both"))
        values_for_threshold.append(sbp)
    if dbp_columns:
        dbp = _numeric_series(df, dbp_columns[0])
        masks.append(dbp.between(4, 25, inclusive="both"))
        values_for_threshold.append(dbp)

    mask = masks[0]
    observed = values_for_threshold[0]
    for next_mask, next_values in zip(masks[1:], values_for_threshold[1:]):
        mask &= next_mask
        observed = observed.where(observed.notna() & next_values.notna())
    mask &= observed.notna()
    if not _is_majority(observed, mask):
        return []

    return [
        _unit_warning(
            issue_id="UNIT_BP_POSSIBLE_KPA",
            variable=", ".join(str(column) for column in columns),
            mask=mask,
            description=(
                "Blood pressure values show a scale pattern consistent with a possible kPa recording "
                "rather than the expected mmHg scale."
            ),
        )
    ]


def _temperature_warnings(df: pd.DataFrame) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for column in df.columns:
        name = _normalize_column(column)
        if "temp" not in name and "temperature" not in name:
            continue
        values = _numeric_series(df, column)
        celsius_label = name.endswith("_c") or "celsius" in name
        fahrenheit_label = name.endswith("_f") or "fahrenheit" in name
        mask = pd.Series(False, index=df.index)
        if celsius_label:
            mask = values.between(86, 113, inclusive="both")
        elif fahrenheit_label:
            mask = values.between(30, 45, inclusive="both")
        if _is_majority(values, mask):
            warnings.append(
                _unit_warning(
                    issue_id="UNIT_TEMPERATURE_F_C_MISMATCH",
                    variable=str(column),
                    mask=mask,
                    description=(
                        "Temperature values show a scale pattern that may indicate a Fahrenheit/Celsius "
                        "mismatch with the column label."
                    ),
                )
            )
    return warnings


def _percent_fraction_warnings(df: pd.DataFrame) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for column in df.columns:
        name = _normalize_column(column)
        values = _numeric_series(df, column)
        percent_label = _has_any(name, {"percent", "percentage", "_pct", "pct_"})
        fraction_label = _has_any(name, {"proportion", "fraction"})
        mask = pd.Series(False, index=df.index)
        if percent_label:
            mask = values.between(0, 1, inclusive="both")
            if not ((values > 0) & (values < 1)).any():
                continue
        elif fraction_label:
            mask = (values > 1) & (values <= 100)
        else:
            continue
        if _is_majority(values, mask):
            warnings.append(
                _unit_warning(
                    issue_id="UNIT_PERCENT_FRACTION_MISMATCH",
                    variable=str(column),
                    mask=mask,
                    description=(
                        "Values show a scale pattern that may indicate a percent-versus-fraction mismatch "
                        "with the column label."
                    ),
                )
            )
    return warnings


def _height_warnings(df: pd.DataFrame) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for column in df.columns:
        name = _normalize_column(column)
        if "height" not in name and "stature" not in name:
            continue
        values = _numeric_series(df, column)
        if name.endswith("_m") or _has_any(name, {"meter", "metre"}):
            mask = values.between(100, 250, inclusive="both")
            issue_id = "UNIT_HEIGHT_CM_AS_M"
            description = "Height values show a scale pattern that may indicate centimeters in a meter-labeled field."
        elif name.endswith("_cm") or _has_any(name, {"centimeter", "centimetre"}):
            mask = values.between(1, 2.5, inclusive="both")
            issue_id = "UNIT_HEIGHT_M_AS_CM"
            description = "Height values show a scale pattern that may indicate meters in a centimeter-labeled field."
        else:
            continue
        if _is_majority(values, mask):
            warnings.append(
                _unit_warning(
                    issue_id=issue_id,
                    variable=str(column),
                    mask=mask,
                    description=description,
                )
            )
    return warnings


def _weight_warnings(df: pd.DataFrame) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for column in df.columns:
        name = _normalize_column(column)
        if "weight" not in name:
            continue
        values = _numeric_series(df, column)
        kg_label = name.endswith("_kg") or "kilogram" in name
        lb_label = name.endswith(("_lb", "_lbs")) or _has_any(name, {"pound", "lbs_"})
        if kg_label:
            mask = values.between(250, 700, inclusive="right")
        elif lb_label:
            mask = values.between(30, 80, inclusive="both")
        else:
            continue
        if _is_majority(values, mask):
            warnings.append(
                _unit_warning(
                    issue_id="UNIT_WEIGHT_LB_AS_KG",
                    variable=str(column),
                    mask=mask,
                    description=(
                        "Weight values show a scale pattern that may indicate a kilograms/pounds mismatch "
                        "with the column label."
                    ),
                )
            )
    return warnings


def _glucose_warnings(df: pd.DataFrame) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for column in df.columns:
        name = _normalize_column(column)
        if not _has_any(name, {"glucose", "fasting_glucose", "blood_glucose", "fbg"}):
            continue
        values = _numeric_series(df, column)
        if _has_any(name, {"mg_dl", "mgdl"}):
            mask = values.between(2, 30, inclusive="both")
        elif _has_any(name, {"mmol_l", "mmoll", "mmol"}):
            mask = values.between(40, 600, inclusive="both")
        else:
            continue
        if _is_majority(values, mask):
            warnings.append(
                _unit_warning(
                    issue_id="UNIT_GLUCOSE_MGDL_MMOLL_MISMATCH",
                    variable=str(column),
                    mask=mask,
                    description=(
                        "Glucose values show a scale pattern that may indicate an mg/dL-versus-mmol/L "
                        "mismatch with the column label."
                    ),
                )
            )
    return warnings


def _creatinine_warnings(df: pd.DataFrame) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for column in df.columns:
        name = _normalize_column(column)
        if not _has_any(name, {"creatinine", "serum_creatinine", "scr"}):
            continue
        values = _numeric_series(df, column)
        if _has_any(name, {"mg_dl", "mgdl"}):
            mask = values.between(20, 2000, inclusive="both")
        elif _has_any(name, {"umol_l", "umoll", "umol"}):
            mask = values.between(0.1, 20, inclusive="both")
        else:
            continue
        if _is_majority(values, mask):
            warnings.append(
                _unit_warning(
                    issue_id="UNIT_CREATININE_MGDL_UMOL_MISMATCH",
                    variable=str(column),
                    mask=mask,
                    description=(
                        "Creatinine values show a scale pattern that may indicate an mg/dL-versus-umol/L "
                        "mismatch with the column label."
                    ),
                )
            )
    return warnings


def _lipid_warnings(df: pd.DataFrame) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    lipid_markers = {"cholesterol", "total_cholesterol", "ldl", "hdl", "triglycerides", "triglyceride", "tg"}
    for column in df.columns:
        name = _normalize_column(column)
        if not _has_any(name, lipid_markers):
            continue
        values = _numeric_series(df, column)
        if _has_any(name, {"mg_dl", "mgdl"}):
            mask = values.between(0.5, 20, inclusive="both")
        elif _has_any(name, {"mmol_l", "mmoll", "mmol"}):
            mask = values.between(30, 1000, inclusive="both")
        else:
            continue
        if _is_majority(values, mask):
            warnings.append(
                _unit_warning(
                    issue_id="UNIT_LIPID_MGDL_MMOLL_MISMATCH",
                    variable=str(column),
                    mask=mask,
                    description=(
                        "Lipid values show a scale pattern that may indicate an mg/dL-versus-mmol/L "
                        "mismatch with the column label."
                    ),
                )
            )
    return warnings


def check_unit_warnings(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Return deterministic warning-only evidence for possible unit or scale mismatches."""
    warnings: list[dict[str, Any]] = []
    warnings.extend(_blood_pressure_warnings(df))
    warnings.extend(_temperature_warnings(df))
    warnings.extend(_percent_fraction_warnings(df))
    warnings.extend(_height_warnings(df))
    warnings.extend(_weight_warnings(df))
    warnings.extend(_glucose_warnings(df))
    warnings.extend(_creatinine_warnings(df))
    warnings.extend(_lipid_warnings(df))
    return warnings
