from __future__ import annotations

from pathlib import Path
from typing import Any


ESTIMATION_METHOD = "approx_chars_div_4"
ESTIMATION_NOTES = "Approximate engineering estimate; not exact tokenizer output."


def estimate_text_tokens(text: str) -> int:
    """Return a rough character-based token estimate with a safe minimum."""
    return max(1, len(text) // 4)


def estimate_file_tokens(path: str | Path | None) -> tuple[int, int | None]:
    """Return estimated tokens and character count for a local text file."""
    if path is None:
        return 1, None

    try:
        text = Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return 1, None
    return estimate_text_tokens(text), len(text)


def build_token_metrics(
    *,
    data_path: str | Path | None,
    report_text: str,
    warning_count: int = 0,
    report_section_count: int = 13,
) -> dict[str, Any]:
    source_tokens, source_character_count = estimate_file_tokens(data_path)
    report_tokens = estimate_text_tokens(report_text)
    return {
        "estimation_method": ESTIMATION_METHOD,
        "source_csv_character_count": source_character_count,
        "source_csv_estimated_tokens": source_tokens,
        "original_csv_estimated_tokens": source_tokens,
        "audit_report_character_count": len(report_text),
        "audit_report_estimated_tokens": report_tokens,
        "compression_ratio": max(0.1, round(source_tokens / report_tokens, 1)),
        "warning_count": max(0, int(warning_count)),
        "report_section_count": max(0, int(report_section_count)),
        "notes": ESTIMATION_NOTES,
    }
