#!/usr/bin/env python3
"""Business Reality Score calculator. Authoritative numeric layer for business-idea-evaluator skill."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def clamp(x: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, x))


def norm10(v: float) -> float:
    return clamp(v) / 10.0


def get_score(experts: dict, agent: str, key: str, default: float = 5.0) -> float:
    try:
        return float(experts[agent]["scores"][key])
    except (KeyError, TypeError, ValueError):
        return default


def get_math(experts: dict, agent: str, key: str, default: float = 0.0) -> float:
    try:
        return float(experts[agent].get("math_params", {}).get(key, default))
    except (TypeError, ValueError):
        return default


def compute_factors(data: dict) -> dict[str, float]:
    e = data.get("experts", {})
    m = data.get("math", {})

    m13 = m.get("13", {})
    m16 = m.get("16", {})

    base_potential = norm10(
        0.25 * get_score(e, "02", "pain_strength")
        + 0.15 * get_score(e, "02", "pain_frequency")
        + 0.25 * get_score(e, "02", "willingness_to_pay")
        + 0.15 * get_score(e, "03", "audience_access")
        + 0.10 * get_score(e, "04", "market_timing")
        + 0.10 * get_score(e, "04", "local_fit")
    )

    evidence_factor = norm10(m13.get("evidence_index", get_score(e, "02", "demand_proof", 3)))
    source_quality = norm10(m13.get("source_quality_index", 5))

    execution = norm10(
        0.4 * get_score(e, "08", "technical_feasibility")
        + 0.35 * get_score(e, "08", "dev_speed")
        + 0.25 * (10 - get_score(e, "08", "external_dependency"))
    )

    money = norm10(
        0.35 * get_score(e, "06", "money_potential")
        + 0.25 * get_score(e, "06", "revenue_repeatability")
        + 0.20 * get_score(e, "06", "monetization_scale")
        + 0.20 * m16.get("financial_feasibility", get_score(e, "06", "money_potential"))
    )

    defense = norm10(
        0.45 * get_score(e, "10", "defensibility")
        + 0.35 * get_score(e, "10", "retention_potential")
        + 0.20 * (10 - get_score(e, "10", "copyability"))
    )

    durability = norm10(
        0.4 * get_score(e, "05", "long_term_potential")
        + 0.3 * (10 - get_score(e, "05", "obsolescence_risk"))
        + 0.3 * (10 - get_score(e, "05", "hype_dependency"))
    )

    max_risk = max(
        get_score(e, "09", "legal_safety", 5),
        get_score(e, "12", "failure_risk", 5),
    )
    risk_penalty = max(0.1, 1.0 - (10 - max_risk) / 10.0)

    fragility = m.get("17", {}).get("fragility_index", get_score(e, "12", "assumption_fragility", 5))
    sensitivity_penalty = max(0.5, 1.0 - (fragility / 10.0) * 0.5)

    return {
        "base_potential": base_potential,
        "evidence_factor": evidence_factor,
        "source_quality": source_quality,
        "execution": execution,
        "money": money,
        "defense": defense,
        "durability": durability,
        "risk_multiplier": risk_penalty,
        "sensitivity_multiplier": sensitivity_penalty,
    }


def apply_blocking_caps(brs: float, data: dict) -> tuple[float, list[str]]:
    e = data.get("experts", {})
    m = data.get("math", {})
    caps: list[str] = []
    cap = 100.0

    legal = get_score(e, "09", "legal_safety")
    wtp = get_score(e, "02", "willingness_to_pay")
    evidence = m.get("13", {}).get("evidence_index", get_score(e, "02", "demand_proof"))
    src_q = m.get("13", {}).get("source_quality_index", 5)
    tech = get_score(e, "08", "technical_feasibility")
    fail = get_score(e, "12", "failure_risk")

    if legal < 3:
        cap = min(cap, 35)
        caps.append("legal_safety < 3 → cap 35")
    if wtp < 4:
        cap = min(cap, 45)
        caps.append("willingness_to_pay < 4 → cap 45")
    if evidence < 3:
        cap = min(cap, 40)
        caps.append("evidence_index < 3 → cap 40 (hypothesis only)")
    if src_q < 3:
        cap = min(cap, 45)
        caps.append("source_quality < 3 → cap 45")
    if tech < 3:
        cap = min(cap, 40)
        caps.append("technical_feasibility < 3 → cap 40")
    if get_math(e, "09", "blocking_legal_risk") >= 1:
        cap = min(cap, 25)
        caps.append("blocking_legal_risk → cap 25")
    if fail >= 8:
        cap = min(cap, 35)
        caps.append("failure_risk ≥ 8 → cap 35")

  # LTV vs CAC
    realistic = m.get("16", {}).get("scenarios", {}).get("realistic", {})
    cac, ltv = realistic.get("cac"), realistic.get("ltv")
    if cac and ltv and ltv < cac:
        cap = min(cap, 30)
        caps.append("LTV < CAC (realistic) → cap 30")

    return min(brs, cap), caps


def compute_brs(data: dict, pessimism: float = 0.0) -> float:
    """pessimism: 0=base, -0.15=min, +0.15=max scenario adjustment on factors."""
    f = compute_factors(data)
    adj = 1.0 + pessimism
    product = (
        f["base_potential"]
        * f["evidence_factor"]
        * f["source_quality"]
        * f["execution"]
        * f["money"]
        * f["defense"]
        * f["durability"]
        * f["risk_multiplier"]
        * f["sensitivity_multiplier"]
        * adj
    )
    return round(product * 100, 1)


def verdict(brs: float) -> str:
    if brs >= 65:
        return "TEST_NARROW_SEGMENT"
    if brs >= 45:
        return "REFORMULATE"
    if brs >= 25:
        return "CHEAP_TESTS_ONLY"
    return "DO_NOT_LAUNCH"


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: calculate_brs.py <biz-eval-input.json>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))

    base = compute_brs(data, 0.0)
    minimum = compute_brs(data, -0.15)
    maximum = compute_brs(data, 0.15)

    base, caps = apply_blocking_caps(base, data)
    minimum, _ = apply_blocking_caps(minimum, data)
    maximum = compute_brs(data, 0.15)
    maximum, _ = apply_blocking_caps(maximum, data)

    m13 = data.get("math", {}).get("13", {})
    m15 = data.get("math", {}).get("15", {})
    m17 = data.get("math", {}).get("17", {})

    confidence = "low"
    sci = m13.get("statistical_confidence_index", 5)
    if sci >= 7:
        confidence = "high"
    elif sci >= 4:
        confidence = "medium"

    out: dict[str, Any] = {
        "business_reality_score": {
            "base": base,
            "min": round(min(minimum, base), 1),
            "max": round(max(maximum, base), 1),
            "confidence": confidence,
            "verdict_code": verdict(base),
        },
        "blocking_caps_applied": caps,
        "factors": compute_factors(data),
        "probability_outcomes": m15.get("outcome_map", {}),
        "top_uncertainty": (m17.get("critical_assumptions") or ["not computed"])[:1],
        "formula": "BRS = BasePotential × Evidence × SourceQuality × Execution × Money × Defense × Durability × Risk × Sensitivity × 100",
    }

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
