from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from pandas.api.types import is_numeric_dtype

from .intake import load_dataset


def _to_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def infer_variable_type(series: pd.Series, column_name: str) -> str:
    non_null = series.dropna()
    if non_null.empty:
        return "empty"

    lower_name = column_name.lower()
    unique_rate = non_null.nunique(dropna=True) / max(len(non_null), 1)

    if "date" in lower_name or lower_name in {"dob", "birth_date", "death_date"}:
        parsed = pd.to_datetime(non_null, errors="coerce")
        if parsed.notna().mean() >= 0.80:
            return "date"

    if "id" in lower_name or unique_rate > 0.95:
        return "identifier-like"

    if is_numeric_dtype(non_null):
        return "numeric"

    avg_length = non_null.astype(str).str.len().mean()
    if avg_length > 40:
        return "free_text-like"

    return "categorical"


def detect_column_types(df: pd.DataFrame) -> dict[str, str]:
    return {column: infer_variable_type(df[column], column) for column in df.columns}


def profile_missingness(df: pd.DataFrame) -> dict[str, dict[str, float | int]]:
    summary = {}
    for column in df.columns:
        missing_count = int(df[column].isna().sum())
        summary[column] = {
            "missing_count": missing_count,
            "missing_rate": round(missing_count / max(len(df), 1), 4),
        }
    return summary


def profile_numeric_variables(df: pd.DataFrame, variable_types: dict[str, str]) -> dict[str, dict[str, float | None]]:
    numeric_summary = {}
    for column in df.columns:
        numeric = pd.to_numeric(df[column], errors="coerce")
        if numeric.notna().sum() == 0:
            continue
        if variable_types.get(column) == "identifier-like" and not is_numeric_dtype(df[column]):
            continue
        numeric_summary[column] = {
            "min": _to_float(numeric.min()),
            "max": _to_float(numeric.max()),
            "mean": round(float(numeric.mean()), 4),
            "median": round(float(numeric.median()), 4),
            "std": round(float(numeric.std()), 4) if numeric.notna().sum() > 1 else None,
        }
    return numeric_summary


def profile_categorical_variables(df: pd.DataFrame, variable_types: dict[str, str]) -> dict[str, dict[str, int]]:
    categorical_summary = {}
    for column in df.columns:
        if variable_types.get(column) in {"categorical", "identifier-like", "free_text-like"}:
            counts = df[column].dropna().astype(str).value_counts().head(8)
            categorical_summary[column] = {str(k): int(v) for k, v in counts.items()}
    return categorical_summary


def profile_date_variables(df: pd.DataFrame, variable_types: dict[str, str]) -> dict[str, dict[str, str | int]]:
    date_summary = {}
    for column, var_type in variable_types.items():
        if var_type == "date":
            parsed = pd.to_datetime(df[column], errors="coerce")
            if parsed.notna().any():
                date_summary[column] = {
                    "min": parsed.min().date().isoformat(),
                    "max": parsed.max().date().isoformat(),
                    "missing_or_invalid_count": int(parsed.isna().sum()),
                }
    return date_summary


def detect_duplicate_records(df: pd.DataFrame, id_column: str = "patient_id") -> dict[str, Any]:
    duplicate_patient_id = 0
    duplicate_patient_id_values: list[str] = []
    if id_column in df.columns:
        duplicated = df[id_column].duplicated(keep=False) & df[id_column].notna()
        duplicate_patient_id = int(duplicated.sum())
        duplicate_patient_id_values = df.loc[duplicated, id_column].astype(str).drop_duplicates().head(10).tolist()

    return {
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_patient_id": duplicate_patient_id,
        "duplicate_patient_id_values": duplicate_patient_id_values,
    }


def detect_potential_id_columns(df: pd.DataFrame, variable_types: dict[str, str] | None = None) -> list[str]:
    variable_types = variable_types or detect_column_types(df)
    return [column for column, var_type in variable_types.items() if var_type == "identifier-like"]


def profile_dataset(df: pd.DataFrame, id_column: str = "patient_id") -> dict[str, Any]:
    variable_types = detect_column_types(df)
    return {
        "n_rows": int(len(df)),
        "n_columns": int(len(df.columns)),
        "columns": list(df.columns),
        "variable_types": variable_types,
        "missing_summary": profile_missingness(df),
        "numeric_summary": profile_numeric_variables(df, variable_types),
        "categorical_summary": profile_categorical_variables(df, variable_types),
        "date_summary": profile_date_variables(df, variable_types),
        "duplicates": detect_duplicate_records(df, id_column=id_column),
        "potential_id_columns": detect_potential_id_columns(df, variable_types),
    }


def load_data(data_path: str | Path) -> pd.DataFrame:
    return load_dataset(data_path)
