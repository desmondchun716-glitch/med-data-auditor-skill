from __future__ import annotations

import pandas as pd

from conftest import load_script


profile_mod = load_script("profile_data_test", "scripts/02_profile_data.py")


def test_profile_dataset_detects_missingness_and_duplicate_patient_id() -> None:
    df = pd.DataFrame(
        {
            "patient_id": ["P1", "P1", "P2"],
            "age": [30, None, 45],
            "visit_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        }
    )

    profile = profile_mod.profile_dataset(df)

    assert profile["n_rows"] == 3
    assert profile["missing_summary"]["age"]["missing_count"] == 1
    assert profile["duplicates"]["duplicate_patient_id"] == 2
    assert profile["variable_types"]["visit_date"] == "date"
