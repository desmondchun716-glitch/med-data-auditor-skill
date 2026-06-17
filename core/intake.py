from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .schemas import make_warning


def load_dataset(path: str | Path) -> pd.DataFrame:
    data_path = Path(path)
    try:
        return pd.read_csv(data_path)
    except UnicodeDecodeError:
        return pd.read_csv(data_path, encoding="utf-8-sig")


def get_file_metadata(path: str | Path) -> dict[str, Any]:
    data_path = Path(path)
    stat = data_path.stat()
    return {
        "path": str(data_path),
        "file_name": data_path.name,
        "size_bytes": int(stat.st_size),
        "suffix": data_path.suffix.lower(),
    }


def preview_column_names(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "columns": list(df.columns),
        "n_columns": int(len(df.columns)),
        "has_duplicate_column_names": bool(pd.Index(df.columns).duplicated().any()),
    }


def intake_dataset(path: str | Path) -> tuple[pd.DataFrame, dict[str, Any], list[dict[str, Any]]]:
    metadata = get_file_metadata(path)
    warnings: list[dict[str, Any]] = []
    if Path(path).suffix.lower() != ".csv":
        warnings.append(
            make_warning(
                "INTAKE_NON_CSV_INPUT",
                "data_quality",
                "medium",
                None,
                "Input file does not have a .csv extension.",
                "v0.1 is designed for CSV input; confirm the file format before auditing.",
                human_confirmation_required=True,
            )
        )

    df = load_dataset(path)
    metadata.update(preview_column_names(df))
    return df, metadata, warnings
