from __future__ import annotations

from core.orchestrator import run_audit
from core.report_generator import generate_markdown_report
from core.token_metrics import build_token_metrics, estimate_text_tokens


def test_estimate_text_tokens_minimum_one() -> None:
    assert estimate_text_tokens("") == 1
    assert estimate_text_tokens("abc") == 1
    assert estimate_text_tokens("abcdefgh") == 2


def test_build_token_metrics_contains_method_and_caveat(tmp_path) -> None:
    data_path = tmp_path / "source.csv"
    data_path.write_text("a,b\n1,2\n", encoding="utf-8")

    metrics = build_token_metrics(
        data_path=data_path,
        report_text="short report",
        warning_count=3,
        report_section_count=13,
    )

    assert metrics["estimation_method"] == "approx_chars_div_4"
    assert metrics["source_csv_character_count"] == len("a,b\n1,2\n")
    assert metrics["audit_report_character_count"] == len("short report")
    assert metrics["warning_count"] == 3
    assert metrics["report_section_count"] == 13
    assert "approximate" in metrics["notes"].lower()
    assert "not exact tokenizer" in metrics["notes"].lower()


def test_build_token_metrics_keeps_backward_compatible_fields() -> None:
    metrics = build_token_metrics(data_path=None, report_text="report")

    assert metrics["source_csv_estimated_tokens"] == metrics["original_csv_estimated_tokens"]
    assert metrics["audit_report_estimated_tokens"] >= 1
    assert isinstance(metrics["compression_ratio"], float)


def test_build_token_metrics_compression_ratio_positive_for_missing_file(tmp_path) -> None:
    metrics = build_token_metrics(
        data_path=tmp_path / "missing.csv",
        report_text="x" * 1000,
    )

    assert metrics["source_csv_character_count"] is None
    assert metrics["source_csv_estimated_tokens"] >= 1
    assert metrics["compression_ratio"] > 0


def test_report_token_summary_mentions_approximate_not_exact() -> None:
    report = generate_markdown_report(
        question="Is BMI associated with hypertension?",
        profile={
            "n_rows": 2,
            "n_columns": 2,
            "variable_types": {"bmi": "numeric", "hypertension": "categorical"},
            "potential_id_columns": [],
            "duplicates": {},
            "missing_summary": {},
            "missingness_readiness": {},
            "categorical_summary": {"hypertension": {"Yes": 1, "No": 1}},
        },
        variable_roles={
            "exposure": ["bmi"],
            "outcome": ["hypertension"],
            "confounders": [],
        },
    )

    assert "Approximate source CSV tokens" in report
    assert "character-count / 4 estimate" in report
    assert "not exact tokenizer output" in report


def test_run_audit_token_metrics_match_final_report(tmp_path) -> None:
    data_path = tmp_path / "source.csv"
    report_path = tmp_path / "report.md"
    data_path.write_text(
        "age,bmi,hypertension\n50,25.0,1\n60,30.0,0\n",
        encoding="utf-8",
    )

    summary = run_audit(
        data_path,
        "Is BMI associated with hypertension after adjusting for age?",
        report_path,
    )
    report = report_path.read_text(encoding="utf-8")
    metrics = summary["token_metrics"]

    assert metrics["audit_report_character_count"] == len(report)
    assert metrics["audit_report_estimated_tokens"] == estimate_text_tokens(report)
