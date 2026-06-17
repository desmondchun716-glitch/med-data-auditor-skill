from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
from types import ModuleType


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent


def _load_script(module_name: str, filename: str) -> ModuleType:
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


profile_mod = _load_script("profile_data", "02_profile_data.py")
medical_mod = _load_script("rule_checks", "03_rule_checks.py")
stat_mod = _load_script("statistical_risk_checks", "04_statistical_risk_checks.py")
variables_mod = _load_script("relevant_variables", "05_relevant_variables.py")
privacy_mod = _load_script("privacy_checks", "06_privacy_checks.py")
report_mod = _load_script("generate_report", "07_generate_report.py")


def run_audit(
    data_path: str | Path,
    question: str,
    output_path: str | Path,
    rules_dir: str | Path | None = None,
) -> Path:
    data_path = Path(data_path)
    output_path = Path(output_path)
    rules_dir = Path(rules_dir) if rules_dir else ROOT_DIR / "rules"

    df = profile_mod.load_data(data_path)
    profile = profile_mod.profile_dataset(df)
    relevant_vars = variables_mod.identify_relevant_variables(
        question,
        list(df.columns),
        dictionary_path=rules_dir / "variable_dictionary.yaml",
    )
    medical_warnings = medical_mod.check_medical_rules(df, rules_path=rules_dir / "medical_rules.yaml")
    statistical_warnings = stat_mod.check_statistical_risks(
        df,
        relevant_vars=relevant_vars,
        rules_path=rules_dir / "statistical_rules.yaml",
    )
    privacy_warnings = privacy_mod.check_privacy_risks(df)
    report = report_mod.generate_markdown_report(
        question=question,
        profile=profile,
        relevant_vars=relevant_vars,
        medical_warnings=medical_warnings,
        statistical_warnings=statistical_warnings,
        privacy_warnings=privacy_warnings,
        data_path=data_path,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a biomedical data audit and generate an AI-ready Markdown report.")
    parser.add_argument("--data", required=True, help="Input CSV dataset.")
    parser.add_argument("--question", required=True, help="Biomedical or public health research question.")
    parser.add_argument("--output", required=True, help="Output Markdown report path.")
    parser.add_argument("--rules-dir", default=str(ROOT_DIR / "rules"), help="Directory containing YAML rules.")
    args = parser.parse_args()

    output = run_audit(args.data, args.question, args.output, args.rules_dir)
    print(f"Wrote audit report to {output}")


if __name__ == "__main__":
    main()
