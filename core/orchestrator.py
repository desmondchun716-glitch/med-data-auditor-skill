from __future__ import annotations

from pathlib import Path
from typing import Any

from .audit_log import build_audit_log, save_audit_log
from .extraction_requests import build_extraction_requests
from .flagged_records import build_flagged_records, save_flagged_records
from .intake import intake_dataset
from .medical_rules import check_medical_rules
from .missingness_readiness import build_missingness_readiness_metrics
from .privacy_checker import check_privacy_risks
from .profiler import profile_dataset
from .report_generator import estimate_token_compression, generate_markdown_report, save_report
from .statistical_risks import check_statistical_risks
from .variable_mapper import generate_study_design_warnings, identify_variable_roles, infer_basic_study_design


ROOT_DIR = Path(__file__).resolve().parents[1]


def run_audit(
    data_path: str | Path,
    question: str,
    output_path: str | Path,
    medical_rules_path: str | Path | None = None,
    statistical_rules_path: str | Path | None = None,
    variable_dictionary_path: str | Path | None = None,
    audit_log_output_path: str | Path | None = None,
    flagged_records_output_path: str | Path | None = None,
) -> dict[str, Any]:
    medical_rules_path = Path(medical_rules_path) if medical_rules_path else ROOT_DIR / "rules" / "medical_rules.yaml"
    statistical_rules_path = Path(statistical_rules_path) if statistical_rules_path else ROOT_DIR / "rules" / "statistical_rules.yaml"
    variable_dictionary_path = Path(variable_dictionary_path) if variable_dictionary_path else ROOT_DIR / "rules" / "variable_dictionary.yaml"

    df, metadata, intake_warnings = intake_dataset(data_path)
    profile = profile_dataset(df)
    variable_roles = identify_variable_roles(question, list(df.columns), dictionary_path=variable_dictionary_path)
    profile["missingness_readiness"] = build_missingness_readiness_metrics(df, variable_roles=variable_roles)
    study_design = infer_basic_study_design(df, list(df.columns))
    study_design_warnings = generate_study_design_warnings(question, variable_roles, study_design)
    medical_warnings = check_medical_rules(df, rules_path=medical_rules_path)
    statistical_warnings = check_statistical_risks(df, profile=profile, variable_roles=variable_roles, rules_path=statistical_rules_path)
    privacy_warnings = check_privacy_risks(df)
    all_warnings = [
        *intake_warnings,
        *study_design_warnings,
        *medical_warnings,
        *statistical_warnings,
        *privacy_warnings,
    ]
    extraction_requests = build_extraction_requests(
        question=question,
        profile=profile,
        variable_roles=variable_roles,
        study_design=study_design,
        warnings=all_warnings,
    )

    report_without_metrics = generate_markdown_report(
        question=question,
        profile=profile,
        variable_roles=variable_roles,
        medical_warnings=intake_warnings + medical_warnings,
        statistical_warnings=statistical_warnings,
        privacy_warnings=privacy_warnings,
        study_design=study_design,
        study_design_warnings=study_design_warnings,
        extraction_requests=extraction_requests,
        data_path=data_path,
    )
    token_metrics = estimate_token_compression(data_path, report_without_metrics)
    report = generate_markdown_report(
        question=question,
        profile=profile,
        variable_roles=variable_roles,
        medical_warnings=intake_warnings + medical_warnings,
        statistical_warnings=statistical_warnings,
        privacy_warnings=privacy_warnings,
        study_design=study_design,
        study_design_warnings=study_design_warnings,
        extraction_requests=extraction_requests,
        token_metrics=token_metrics,
        data_path=data_path,
    )
    save_report(report, output_path)

    audit_log = None
    if audit_log_output_path:
        audit_log = build_audit_log(
            data_path=data_path,
            question=question,
            output_path=output_path,
            audit_log_output_path=audit_log_output_path,
            metadata=metadata,
            profile=profile,
            variable_roles=variable_roles,
            study_design=study_design,
            extraction_requests=extraction_requests,
            intake_warnings=intake_warnings,
            study_design_warnings=study_design_warnings,
            medical_warnings=medical_warnings,
            statistical_warnings=statistical_warnings,
            privacy_warnings=privacy_warnings,
            token_metrics=token_metrics,
            rule_paths={
                "medical_rules": medical_rules_path,
                "statistical_rules": statistical_rules_path,
                "variable_dictionary": variable_dictionary_path,
            },
        )
        save_audit_log(audit_log, audit_log_output_path)

    flagged_records = None
    if flagged_records_output_path:
        flagged_records = build_flagged_records(all_warnings)
        save_flagged_records(flagged_records, flagged_records_output_path)

    return {
        "output_path": str(output_path),
        "audit_log_path": str(audit_log_output_path) if audit_log_output_path else None,
        "audit_log": audit_log,
        "flagged_records_path": str(flagged_records_output_path) if flagged_records_output_path else None,
        "flagged_records_count": len(flagged_records) if flagged_records is not None else None,
        "metadata": metadata,
        "profile": profile,
        "variable_roles": variable_roles,
        "study_design": study_design,
        "extraction_requests": extraction_requests,
        "warning_counts": {
            "intake": len(intake_warnings),
            "study_design": len(study_design_warnings),
            "medical": len(medical_warnings),
            "statistical": len(statistical_warnings),
            "privacy": len(privacy_warnings),
        },
        "token_metrics": token_metrics,
    }
