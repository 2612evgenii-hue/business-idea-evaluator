#!/usr/bin/env python3
"""Validate biz-eval-input.json before scoring. Exits non-zero on hard errors."""

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


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: validate_input.py <biz-eval-input.json>", file=sys.stderr)
        sys.exit(2)

    errors: list[str] = []
    warnings: list[str] = []

    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FATAL: cannot read/parse JSON: {exc}", file=sys.stderr)
        sys.exit(2)

    if not data.get("idea_brief"):
        warnings.append("idea_brief is empty")

    experts = data.get("experts", {})
    for eid in REQUIRED_EXPERTS:
        if eid not in experts:
            errors.append(f"missing expert {eid}")
            continue
        scores = experts[eid].get("scores", {})
        for key in EXPERT_SCORE_KEYS.get(eid, []):
            if key not in scores:
                warnings.append(f"expert {eid}: missing score '{key}' (will default to 5)")
                continue
            val = scores[key]
            if not isinstance(val, (int, float)) or not (0 <= val <= 10):
                errors.append(f"expert {eid}.{key} = {val!r} not in 0..10")

    math = data.get("math", {})
    for mid in REQUIRED_MATH:
        if mid not in math:
            warnings.append(f"missing math agent {mid} (scoring will use fallbacks)")

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        print(f"\nFAILED: {len(errors)} hard error(s), {len(warnings)} warning(s)", file=sys.stderr)
        sys.exit(1)
    print(f"\nOK: input valid ({len(warnings)} warning(s))")


if __name__ == "__main__":
    main()
