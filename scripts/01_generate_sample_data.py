from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd


DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "data" / "sample_medical_data.csv"


def generate_sample_data(n_rows: int = 300, seed: int = 42) -> pd.DataFrame:
    rng = random.Random(seed)
    start_date = date(2024, 1, 1)
    rows = []

    for i in range(n_rows):
        age = rng.randint(20, 85)
        sex = rng.choice(["Male", "Female", "male", "M", "F", "1", "0"])
        height_cm = rng.randint(150, 190)
        weight_kg = round(rng.uniform(48, 105), 1)
        bmi = round(weight_kg / ((height_cm / 100) ** 2), 1)
        sbp = rng.randint(105, 165)
        dbp = rng.randint(65, 100)
        smoking = rng.choice(["Never", "Former", "Current"])
        diabetes = rng.choice(["No", "No", "No", "Yes"])
        hypertension = "Yes" if rng.random() < 0.08 else "No"
        visit_date = start_date + timedelta(days=rng.randint(0, 180))
        death_date = "" if rng.random() < 0.95 else (visit_date + timedelta(days=rng.randint(5, 300))).isoformat()
        follow_up_days = rng.randint(30, 420)
        treatment_group = rng.choice(["A", "B"])
        outcome = rng.choice(["Improved", "Not improved"])

        rows.append(
            {
                "patient_id": f"P{i + 1:04d}",
                "patient_name": f"Synthetic Patient {i + 1}",
                "email": f"synthetic{i + 1}@example.test",
                "age": age,
                "sex": sex,
                "height_cm": height_cm,
                "weight_kg": weight_kg,
                "bmi": bmi,
                "sbp": sbp,
                "dbp": dbp,
                "smoking": smoking,
                "diabetes": diabetes,
                "hypertension": hypertension,
                "visit_date": visit_date.isoformat(),
                "death_date": death_date,
                "follow_up_days": follow_up_days,
                "treatment_group": treatment_group,
                "outcome": outcome,
            }
        )

    df = pd.DataFrame(rows)

    # Inject deterministic issues for validation and GitHub demonstration.
    df.loc[0, "age"] = 150
    df.loc[1, "age"] = -3
    df.loc[2, "bmi"] = 5
    df.loc[3, "bmi"] = 90
    df.loc[4, ["sbp", "dbp"]] = [80, 120]
    df.loc[5, ["visit_date", "death_date"]] = ["2024-05-20", "2024-02-01"]
    df.loc[6, "follow_up_days"] = -20
    df.loc[30, "patient_id"] = df.loc[29, "patient_id"]
    df.loc[31, "patient_id"] = df.loc[29, "patient_id"]
    df.loc[40:109, "bmi"] = None
    df.loc[120:122, "hypertension"] = None

    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic biomedical sample data.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output CSV path.")
    parser.add_argument("--rows", type=int, default=300, help="Number of synthetic rows.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_sample_data(n_rows=args.rows, seed=args.seed)
    df.to_csv(output_path, index=False)
    print(f"Wrote {len(df)} synthetic rows to {output_path}")


if __name__ == "__main__":
    main()
