from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parent / "01_generate_sample_data.py"
SPEC = importlib.util.spec_from_file_location("generate_sample_data_legacy", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Could not load {SCRIPT_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

generate_sample_data = MODULE.generate_sample_data
main = MODULE.main


if __name__ == "__main__":
    main()
