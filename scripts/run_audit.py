from __future__ import annotations

import argparse
from pathlib import Path

from core.orchestrator import ROOT_DIR, run_audit


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a biomedical data audit and generate an AI-ready Markdown report.")
    parser.add_argument("--data", required=True, help="Input CSV dataset.")
    parser.add_argument("--question", required=True, help="Biomedical or public health research question.")
    parser.add_argument("--output", required=True, help="Output Markdown report path.")
    parser.add_argument("--rules-dir", default=str(ROOT_DIR / "rules"), help="Directory containing YAML rules.")
    args = parser.parse_args()

    rules_dir = Path(args.rules_dir)
    summary = run_audit(
        args.data,
        args.question,
        args.output,
        medical_rules_path=rules_dir / "medical_rules.yaml",
        statistical_rules_path=rules_dir / "statistical_rules.yaml",
        variable_dictionary_path=rules_dir / "variable_dictionary.yaml",
    )
    print(f"Wrote audit report to {summary['output_path']}")


if __name__ == "__main__":
    main()
