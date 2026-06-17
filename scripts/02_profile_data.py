from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from pandas.api.types import is_numeric_dtype


def load_data(data_path: str | Path) -> pd.DataFrame:
    return pd.read_csv(data_path)


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


def profile_dataset(df: pd.DataFrame, id_column: str = "patient_id") -> dict[str, Any]:
    variable_types = {column: infer_variable_type(df[column], column) for column in df.columns}

    missing_summary = {}
    for column in df.columns:
        missing_count = int(df[column].isna().sum())
        missing_summary[column] = {
            "missing_count": missing_count,
            "missing_rate": round(missing_count / max(len(df), 1), 4),
        }

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

    categorical_summary = {}
    for column in df.columns:
        if variable_types.get(column) in {"categorical", "identifier-like", "free_text-like"}:
            counts = df[column].dropna().astype(str).value_counts().head(8)
            categorical_summary[column] = {str(k): int(v) for k, v in counts.items()}

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

    duplicate_patient_id = 0
    duplicate_patient_id_values: list[str] = []
    if id_column in df.columns:
        duplicated = df[id_column].duplicated(keep=False) & df[id_column].notna()
        duplicate_patient_id = int(duplicated.sum())
        duplicate_patient_id_values = df.loc[duplicated, id_column].astype(str).drop_duplicates().head(10).tolist()

    return {
        "n_rows": int(len(df)),
        "n_columns": int(len(df.columns)),
        "columns": list(df.columns),
        "variable_types": variable_types,
        "missing_summary": missing_summary,
        "numeric_summary": numeric_summary,
        "categorical_summary": categorical_summary,
        "date_summary": date_summary,
        "duplicates": {
            "duplicate_rows": int(df.duplicated().sum()),
            "duplicate_patient_id": duplicate_patient_id,
            "duplicate_patient_id_values": duplicate_patient_id_values,
        },
    }
