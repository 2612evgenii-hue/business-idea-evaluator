#!/usr/bin/env python3
"""Backward-compatible alias for validate_evidence_package.py.

The canonical validator is `validate_evidence_package.py`. This shim is kept so
older instructions/scripts that call `validate_input.py` keep working.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    target = Path(__file__).resolve().parent / "validate_evidence_package.py"
    sys.argv[0] = str(target)
    runpy.run_path(str(target), run_name="__main__")
