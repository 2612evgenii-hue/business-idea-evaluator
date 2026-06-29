#!/usr/bin/env python3
"""Business Reality Score (BRS) calculator.

Authoritative, deterministic numeric layer for the business-idea-evaluator skill.

Design rules (do not regress):
- NOT an arithmetic mean. A mean hides blocking weaknesses.
- NOT a raw product of nine sub-1.0 factors (that underflows toward zero).
- Uses a WEIGHTED GEOMETRIC MEAN of nine normalized factors, then applies hard
  blocking caps. A single very low factor still drags the score down sharply,
  while fatal conditions (legal, no willingness to pay, no evidence, LTV<CAC...)
  are enforced as explicit ceilings.
- Safety scores ("higher = better", e.g. legal_safety) and risk scores
  ("higher = worse", e.g. failure_risk) are normalized into the SAME direction
  before they are combined. They must never be added as if identical.
- Stdlib only. Deterministic. No network.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

# Weights for the geometric mean. Money and risk carry more pull because a
# business that cannot make money or is legally/operationally fatal should not
# score well even if everything else is strong.
FACTOR_WEIGHTS: dict[str, float] = {
    "base_potential": 1.3,
    "evidence_factor": 1.1,
    "source_quality": 0.9,
    "execution": 1.0,
    "money": 1.4,
    "defense": 0.9,
    "durability": 0.9,
    "risk_multiplier": 1.4,
    "sensitivity_multiplier": 1.1,
}

EPS = 1e-6


def clamp(x: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, x))


def norm10(v: float) -> float:
    return clamp(v) / 10.0


def get_score(experts: dict, agent: str, key: str, default: float = 5.0) -> float:
    try:
        return float(experts[agent]["scores"][key])
    except (KeyError, TypeError, ValueError):
        return default


def get_math_param(experts: dict, agent: str, key: str, default: float = 0.0) -> float:
    try:
        return float(experts[agent].get("math_params", {}).get(key, default))
    except (TypeError, ValueError):
        return default


# --------------------------------------------------------------------------- #
# Input validation (collects warnings; never crashes silently)
# --------------------------------------------------------------------------- #

REQUIRED_EXPERTS = [f"{i:02d}" for i in range(1, 13)]
REQUIRED_MATH = [str(i) for i in range(13, 19)]


def validate(data: dict) -> list[str]:
    """Return human-readable warnings. Out-of-range numbers are clamped at use."""
    warns: list[str] = []
    if not data.get("idea_brief"):
        warns.append("idea_brief is empty")

    experts = data.get("experts", {})
    for eid in REQUIRED_EXPERTS:
        if eid not in experts:
            warns.append(f"missing expert {eid} (scores default to 5)")
            continue
        for key, val in (experts[eid].get("scores") or {}).items():
            if not isinstance(val, (int, float)):
                warns.append(f"expert {eid}.{key} is not numeric ({val!r})")
            elif not (0 <= val <= 10):
                warns.append(f"expert {eid}.{key}={val} out of 0..10 (clamped)")

    math_block = data.get("math", {})
    for mid in REQUIRED_MATH:
        if mid not in math_block:
            warns.append(f"missing math agent {mid} (uses fallbacks)")

    if count_sources(data) == 0:
        warns.append("no sources provided in any expert output (source quality penalized)")
    if data.get("internet_available") is False:
        warns.append("internet_available=false: market claims treated as hypotheses")
    return warns


def count_sources(data: dict) -> int:
    n = 0
    for e in (data.get("experts") or {}).values():
        srcs = e.get("sources")
        if isinstance(srcs, list):
            n += len([s for s in srcs if isinstance(s, dict) and s.get("url")])
    return n


# --------------------------------------------------------------------------- #
# Factors (all normalized to [0,1])
# --------------------------------------------------------------------------- #


def compute_factors(data: dict) -> dict[str, float]:
    e = data.get("experts", {})
    m = data.get("math", {})
    m13 = m.get("13", {})
    m16 = m.get("16", {})
    m17 = m.get("17", {})

    base_potential = norm10(
        0.25 * get_score(e, "02", "pain_strength")
        + 0.15 * get_score(e, "02", "pain_frequency")
        + 0.25 * get_score(e, "02", "willingness_to_pay")
        + 0.15 * get_score(e, "03", "audience_access")
        + 0.10 * get_score(e, "04", "market_timing")
        + 0.10 * get_score(e, "04", "local_fit")
    )

    evidence_factor = norm10(m13.get("evidence_index", get_score(e, "02", "demand_proof", 3)))

    # Source quality: start from math agent 13, then penalize hard when no real
    # sources exist or internet was unavailable (honesty over optimism).
    source_quality = norm10(m13.get("source_quality_index", 5))
    if count_sources(data) == 0:
        source_quality = min(source_quality, 0.3)
    if data.get("internet_available") is False:
        source_quality = min(source_quality, 0.3)

    execution = norm10(
        0.40 * get_score(e, "08", "technical_feasibility")
        + 0.35 * get_score(e, "08", "dev_speed")
        + 0.25 * (10 - get_score(e, "08", "external_dependency"))
    )

    # Money = revenue-model strength, gated by real unit economics (LTV/CAC,
    # margin, payback). A model where LTV < CAC must drag Money down even if the
    # qualitative revenue scores are high.
    money_base = norm10(
        0.30 * get_score(e, "06", "money_potential")
        + 0.25 * get_score(e, "06", "revenue_repeatability")
        + 0.20 * get_score(e, "06", "monetization_scale")
        + 0.25 * m16.get("financial_feasibility", get_score(e, "06", "money_potential"))
    )
    money = money_base * unit_econ_modifier(m16)

    defense = norm10(
        0.45 * get_score(e, "10", "defensibility")
        + 0.35 * get_score(e, "10", "retention_potential")
        + 0.20 * (10 - get_score(e, "10", "copyability"))
    )

    durability = norm10(
        0.40 * get_score(e, "05", "long_term_potential")
        + 0.30 * (10 - get_score(e, "05", "obsolescence_risk"))
        + 0.30 * (10 - get_score(e, "05", "hype_dependency"))
    )

    # Risk: convert "higher = safer" scores into "higher = riskier" first, then
    # take the worst risk dimension. legal_safety 10 (good) and failure_risk 10
    # (bad) must NOT be summed in the same direction.
    legal_risk = 10.0 - get_score(e, "09", "legal_safety", 5)
    platform_risk = 10.0 - get_score(e, "09", "platform_stability", 5)
    failure_risk = get_score(e, "12", "failure_risk", 5)
    kill_severity = get_score(e, "12", "kill_shot_severity", failure_risk)
    max_risk = max(legal_risk, platform_risk, failure_risk, kill_severity)
    risk_multiplier = max(0.1, 1.0 - max_risk / 10.0)

    fragility = m17.get("fragility_index", get_score(e, "12", "assumption_fragility", 5))
    sensitivity_multiplier = max(0.5, 1.0 - (clamp(fragility) / 10.0) * 0.5)

    return {
        "base_potential": round(base_potential, 4),
        "evidence_factor": round(evidence_factor, 4),
        "source_quality": round(source_quality, 4),
        "execution": round(execution, 4),
        "money": round(money, 4),
        "defense": round(defense, 4),
        "durability": round(durability, 4),
        "risk_multiplier": round(risk_multiplier, 4),
        "sensitivity_multiplier": round(sensitivity_multiplier, 4),
    }


def unit_econ_modifier(m16: dict) -> float:
    """Multiplier in [0.4, 1.0] derived from realistic-scenario unit economics."""
    realistic = (m16.get("scenarios") or {}).get("realistic") or {}
    cac = realistic.get("cac")
    ltv = realistic.get("ltv")
    margin = realistic.get("gross_margin_pct")
    payback = realistic.get("payback_months")

    mod = 1.0
    if cac and ltv and cac > 0:
        ratio = ltv / cac
        if ratio >= 3.0:
            mod *= 1.0
        elif ratio >= 1.0:
            mod *= 0.7 + 0.1 * (ratio - 1.0)  # 0.7..0.9 across 1x..3x
        else:
            mod *= max(0.4, 0.4 + 0.3 * ratio)  # ratio<1 -> 0.4..0.7
    if isinstance(margin, (int, float)) and margin < 40:
        mod *= 0.85
    if isinstance(payback, (int, float)) and payback > 18:
        mod *= 0.85
    return max(0.4, min(1.0, mod))


# --------------------------------------------------------------------------- #
# Blocking caps
# --------------------------------------------------------------------------- #


def apply_blocking_caps(brs: float, data: dict) -> tuple[float, list[str]]:
    e = data.get("experts", {})
    m = data.get("math", {})
    caps: list[str] = []
    cap = 100.0

    legal = get_score(e, "09", "legal_safety")
    wtp = get_score(e, "02", "willingness_to_pay")
    evidence = m.get("13", {}).get("evidence_index", get_score(e, "02", "demand_proof"))
    src_q = m.get("13", {}).get("source_quality_index", 5)
    if count_sources(data) == 0 or data.get("internet_available") is False:
        src_q = min(src_q, 3)
    tech = get_score(e, "08", "technical_feasibility")
    fail = get_score(e, "12", "failure_risk")

    def add(condition: bool, value: float, label: str) -> None:
        nonlocal cap
        if condition:
            cap = min(cap, value)
            caps.append(label)

    add(legal < 3, 35, "legal_safety < 3 → cap 35")
    add(wtp < 4, 45, "willingness_to_pay < 4 → cap 45")
    add(evidence < 3, 40, "evidence_index < 3 → cap 40 (hypothesis only)")
    add(src_q < 3, 45, "source_quality < 3 → cap 45")
    add(tech < 3, 40, "technical_feasibility < 3 → cap 40")
    add(get_math_param(e, "09", "blocking_legal_risk") >= 1, 25, "blocking_legal_risk → cap 25")
    add(fail >= 8, 35, "failure_risk ≥ 8 → cap 35")

    realistic = (m.get("16", {}).get("scenarios") or {}).get("realistic") or {}
    cac, ltv = realistic.get("cac"), realistic.get("ltv")
    add(bool(cac) and bool(ltv) and ltv < cac, 30, "LTV < CAC (realistic) → cap 30")

    return min(brs, cap), caps


# --------------------------------------------------------------------------- #
# BRS computation
# --------------------------------------------------------------------------- #


def compute_brs(data: dict, pessimism: float = 0.0) -> float:
    """Weighted geometric mean of nine factors, scaled to 0-100.

    pessimism shifts the result for min/max scenarios (-0.15 .. +0.15).
    """
    f = compute_factors(data)
    weighted_log = 0.0
    weight_sum = 0.0
    for name, weight in FACTOR_WEIGHTS.items():
        weighted_log += weight * math.log(max(f[name], EPS))
        weight_sum += weight
    geo = math.exp(weighted_log / weight_sum)
    geo *= 1.0 + pessimism
    return round(min(max(geo, 0.0), 1.0) * 100, 1)


def verdict(brs: float) -> str:
    if brs >= 65:
        return "TEST_NARROW_SEGMENT"
    if brs >= 45:
        return "REFORMULATE"
    if brs >= 25:
        return "CHEAP_TESTS_ONLY"
    return "DO_NOT_LAUNCH"


def confidence_label(data: dict) -> str:
    m13 = data.get("math", {}).get("13", {})
    sci = m13.get("statistical_confidence_index", 5)
    evidence = m13.get("evidence_index", get_score(data.get("experts", {}), "02", "demand_proof", 3))
    score = min(sci, evidence)
    if score >= 7:
        return "high"
    if score >= 4:
        return "medium"
    return "low"


def diagnose(data: dict, factors: dict[str, float], caps: list[str]) -> dict[str, Any]:
    """Identify the dominant blocker, growth lever, and uncertainty."""
    e = data.get("experts", {})
    m = data.get("math", {})

    potentials = {
        "base_potential": factors["base_potential"],
        "execution": factors["execution"],
        "money": factors["money"],
        "defense": factors["defense"],
        "durability": factors["durability"],
    }
    main_growth_factor = max(potentials, key=potentials.get)

    # Blocking risk: prefer the binding cap; else worst risk dimension.
    risks = {
        "legal_risk": 10.0 - get_score(e, "09", "legal_safety", 5),
        "platform_risk": 10.0 - get_score(e, "09", "platform_stability", 5),
        "failure_risk": get_score(e, "12", "failure_risk", 5),
    }
    if caps:
        main_blocking_risk = caps[0]
    else:
        worst = max(risks, key=risks.get)
        main_blocking_risk = f"{worst} = {risks[worst]:.0f}/10"

    crit = m.get("17", {}).get("critical_assumptions") or []
    main_uncertainty = crit[0] if crit else m.get("18", {}).get("priority_hypothesis", "not computed")

    return {
        "main_growth_factor": main_growth_factor,
        "main_blocking_risk": main_blocking_risk,
        "main_uncertainty_factor": main_uncertainty,
    }


def build_report(data: dict) -> dict[str, Any]:
    warnings = validate(data)
    factors = compute_factors(data)

    base = compute_brs(data, 0.0)
    minimum = compute_brs(data, -0.15)
    maximum = compute_brs(data, 0.15)

    base, caps = apply_blocking_caps(base, data)
    minimum, _ = apply_blocking_caps(minimum, data)
    maximum, _ = apply_blocking_caps(maximum, data)

    m13 = data.get("math", {}).get("13", {})
    m15 = data.get("math", {}).get("15", {})

    evidence_index = m13.get("evidence_index", get_score(data.get("experts", {}), "02", "demand_proof", 3))
    hypothetical = evidence_index < 3 or factors["source_quality"] < 0.3

    diag = diagnose(data, factors, caps)

    return {
        "business_reality_score": {
            "base": base,
            "min": round(min(minimum, base), 1),
            "max": round(max(maximum, base), 1),
            "confidence": confidence_label(data),
            "verdict_code": verdict(base),
        },
        "evidence_index": round(float(evidence_index), 1),
        "source_quality_index": round(factors["source_quality"] * 10, 1),
        "hypothetical": hypothetical,
        "blocking_caps_applied": caps,
        "main_blocking_risk": diag["main_blocking_risk"],
        "main_growth_factor": diag["main_growth_factor"],
        "main_uncertainty_factor": diag["main_uncertainty_factor"],
        "factors": factors,
        "probability_map": m15.get("outcome_map", {}),
        "scenarios": m15.get("scenarios", {}),
        "warnings": warnings,
        "formula": (
            "BRS = 100 × weighted_geomean(base_potential, evidence_factor, "
            "source_quality, execution, money, defense, durability, "
            "risk_multiplier, sensitivity_multiplier), then blocking caps"
        ),
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: calculate_brs.py <biz-eval-input.json>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FATAL: cannot read/parse JSON: {exc}", file=sys.stderr)
        sys.exit(2)

    print(json.dumps(build_report(data), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
