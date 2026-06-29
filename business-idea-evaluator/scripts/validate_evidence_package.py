#!/usr/bin/env python3
"""Validate an Expert Evidence Package (BRS input) before scoring.

- Dependency-free core validation (works everywhere, stdlib only).
- If `jsonschema` is installed, ALSO validates against
  references/evidence-package.schema.json for full structural checks.

Exit codes: 0 = valid (warnings allowed), 1 = hard errors, 2 = unreadable input.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_EXPERTS = [f"{i:02d}" for i in range(1, 13)]
REQUIRED_MATH = [str(i) for i in range(13, 19)]

EXPERT_SCORE_KEYS = {
    "01": ["novelty", "competition_saturation", "search_confidence"],
    "02": ["pain_strength", "pain_frequency", "willingness_to_pay", "demand_proof"],
    "03": ["audience_access", "sales_difficulty", "decision_speed"],
    "04": ["market_timing", "country_risk", "local_fit"],
    "05": ["long_term_potential", "hype_dependency", "obsolescence_risk"],
    "06": ["money_potential", "revenue_repeatability", "monetization_scale"],
    "07": ["marketing_difficulty", "organic_growth", "product_trust"],
    "08": ["technical_feasibility", "dev_speed", "external_dependency"],
    "09": ["legal_safety", "platform_stability", "ethical_cleanliness"],
    "10": ["defensibility", "copyability", "retention_potential"],
    "11": ["startup_practicality", "validation_speed", "first_sales_difficulty"],
    "12": ["failure_risk", "assumption_fragility", "kill_shot_severity"],
}

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "references" / "evidence-package.schema.json"


def core_validate(data: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(data, dict):
        return ["root is not a JSON object"], warnings

    if not data.get("idea_brief"):
        warnings.append("idea_brief is empty")

    experts = data.get("experts")
    if not isinstance(experts, dict):
        errors.append("'experts' object missing")
        experts = {}
    for eid in REQUIRED_EXPERTS:
        if eid not in experts:
            errors.append(f"missing expert {eid}")
            continue
        scores = experts[eid].get("scores", {})
        if not isinstance(scores, dict) or not scores:
            errors.append(f"expert {eid}: 'scores' missing or empty")
            continue
        for key in EXPERT_SCORE_KEYS.get(eid, []):
            if key not in scores:
                warnings.append(f"expert {eid}: missing score '{key}' (defaults to 5)")
                continue
            val = scores[key]
            if not isinstance(val, (int, float)) or isinstance(val, bool) or not (0 <= val <= 10):
                errors.append(f"expert {eid}.{key} = {val!r} not a number in 0..10")
        if not experts[eid].get("sources"):
            warnings.append(f"expert {eid}: no sources (claims treated as weaker evidence)")

    math_block = data.get("math")
    if not isinstance(math_block, dict):
        errors.append("'math' object missing")
        math_block = {}
    for mid in REQUIRED_MATH:
        if mid not in math_block:
            warnings.append(f"missing math agent {mid} (scoring uses fallbacks)")

    if data.get("internet_available") is False:
        warnings.append("internet_available=false: source quality will be capped")

    return errors, warnings


def schema_validate(data: dict) -> list[str]:
    """Returns schema errors if jsonschema is available; else empty (skipped)."""
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return []
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot load schema: {exc}"]
    validator = jsonschema.Draft7Validator(schema)
    return [f"schema: {e.json_path}: {e.message}" for e in validator.iter_errors(data)]


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: validate_evidence_package.py <evidence-package.json>", file=sys.stderr)
        sys.exit(2)

    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FATAL: cannot read/parse JSON: {exc}", file=sys.stderr)
        sys.exit(2)

    errors, warnings = core_validate(data)
    errors += schema_validate(data)

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        print(f"\nFAILED: {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        sys.exit(1)
    print(f"\nOK: evidence package valid ({len(warnings)} warning(s))")


if __name__ == "__main__":
    main()
