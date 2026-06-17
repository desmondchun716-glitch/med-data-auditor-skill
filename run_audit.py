from __future__ import annotations

import argparse
from pathlib import Path

from core.orchestrator import ROOT_DIR, run_audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a biomedical data analysis-readiness audit and generate an AI-ready Markdown report.",
    )
    parser.add_argument("--data", required=True, help="Input CSV dataset path.")
    parser.add_argument("--question", required=True, help="Biomedical or public health research question.")
    parser.add_argument("--output", required=True, help="Output Markdown report path.")
    parser.add_argument("--rules-dir", default=str(ROOT_DIR / "rules"), help="Directory containing YAML rule files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rules_dir = Path(args.rules_dir)
    summary = run_audit(
        args.data,
        args.question,
        args.output,
        medical_rules_path=rules_dir / "medical_rules.yaml",
        statistical_rules_path=rules_dir / "statistical_rules.yaml",
        variable_dictionary_path=rules_dir / "variable_dictionary.yaml",
    )

    warning_counts = summary["warning_counts"]
    print(f"Wrote audit report to {summary['output_path']}")
    print(
        "Warnings: "
        f"intake={warning_counts['intake']}, "
        f"medical={warning_counts['medical']}, "
        f"statistical={warning_counts['statistical']}, "
        f"privacy={warning_counts['privacy']}, "
        f"study_design={warning_counts['study_design']}"
    )
    metrics = summary["token_metrics"]
    print(
        "Approximate token compression: "
        f"{metrics['original_csv_estimated_tokens']} -> "
        f"{metrics['audit_report_estimated_tokens']} "
        f"({metrics['compression_ratio']}:1)"
    )


if __name__ == "__main__":
    main()
