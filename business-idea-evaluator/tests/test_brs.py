"""Test suite for the Business Reality Score layer.

Run from the repo root or the skill root:  pytest

Covers the 10 required guarantees:
 1. calculate_brs.py runs on the example input.
 2. example-input.json is a valid evidence package.
 3. BRS is always within 0..100.
 4. Low evidence lowers the result.
 5. High legal risk lowers the result.
 6. CAC > LTV lowers the Money factor.
 7. High copyability lowers the Defense factor.
 8. A single fragile unproven assumption lowers the result.
 9. Missing sources lowers the Source Quality factor.
10. The formula is NOT a simple arithmetic mean.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_ROOT / "scripts"
EXAMPLE = SKILL_ROOT / "references" / "example-input.json"

sys.path.insert(0, str(SCRIPTS))

import calculate_brs as brs  # noqa: E402


@pytest.fixture()
def base_data() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def _brs(data: dict) -> float:
    return brs.build_report(data)["business_reality_score"]["base"]


# 1
def test_script_runs_on_example():
    out = subprocess.run(
        [sys.executable, str(SCRIPTS / "calculate_brs.py"), str(EXAMPLE)],
        capture_output=True, text=True,
    )
    assert out.returncode == 0, out.stderr
    parsed = json.loads(out.stdout)
    assert "business_reality_score" in parsed


# 2
def test_example_input_is_valid():
    out = subprocess.run(
        [sys.executable, str(SCRIPTS / "validate_evidence_package.py"), str(EXAMPLE)],
        capture_output=True, text=True,
    )
    assert out.returncode == 0, out.stderr


# 3
def test_brs_within_bounds(base_data):
    report = brs.build_report(base_data)
    s = report["business_reality_score"]
    for key in ("base", "min", "max"):
        assert 0 <= s[key] <= 100


# 4
def test_low_evidence_lowers_score(base_data):
    high = copy.deepcopy(base_data)
    high["math"]["13"]["evidence_index"] = 8
    low = copy.deepcopy(base_data)
    low["math"]["13"]["evidence_index"] = 1
    assert _brs(low) < _brs(high)


# 5
def test_high_legal_risk_lowers_score(base_data):
    safe = copy.deepcopy(base_data)
    safe["experts"]["09"]["scores"]["legal_safety"] = 9
    unsafe = copy.deepcopy(base_data)
    unsafe["experts"]["09"]["scores"]["legal_safety"] = 1
    assert _brs(unsafe) < _brs(safe)
    # and the blocking cap fires
    report = brs.build_report(unsafe)
    assert report["business_reality_score"]["base"] <= 35


# 6
def test_cac_above_ltv_lowers_money(base_data):
    good = copy.deepcopy(base_data)
    good["math"]["16"]["scenarios"]["realistic"] = {"cac": 200, "ltv": 1000}
    bad = copy.deepcopy(base_data)
    bad["math"]["16"]["scenarios"]["realistic"] = {"cac": 1000, "ltv": 200}
    assert brs.compute_factors(bad)["money"] < brs.compute_factors(good)["money"]


# 7
def test_high_copyability_lowers_defense(base_data):
    protected = copy.deepcopy(base_data)
    protected["experts"]["10"]["scores"]["copyability"] = 1
    copyable = copy.deepcopy(base_data)
    copyable["experts"]["10"]["scores"]["copyability"] = 10
    assert brs.compute_factors(copyable)["defense"] < brs.compute_factors(protected)["defense"]


# 8
def test_fragile_assumption_lowers_score(base_data):
    robust = copy.deepcopy(base_data)
    robust["math"]["17"]["fragility_index"] = 1
    fragile = copy.deepcopy(base_data)
    fragile["math"]["17"]["fragility_index"] = 10
    assert _brs(fragile) < _brs(robust)
    assert brs.compute_factors(fragile)["sensitivity_multiplier"] < brs.compute_factors(robust)["sensitivity_multiplier"]


# 9
def test_missing_sources_lowers_source_quality(base_data):
    with_sources = copy.deepcopy(base_data)
    with_sources["experts"]["02"]["sources"] = [
        {"url": "https://example.com/proof", "confirms": "demand"}
    ]
    without = copy.deepcopy(base_data)
    for e in without["experts"].values():
        e.pop("sources", None)
    assert brs.compute_factors(without)["source_quality"] < brs.compute_factors(with_sources)["source_quality"]


# Monte Carlo: deterministic for a fixed seed, and wider when evidence is weak.
def test_monte_carlo_is_deterministic(base_data):
    a = brs.monte_carlo(base_data, simulations=500, seed=42)
    b = brs.monte_carlo(base_data, simulations=500, seed=42)
    assert a == b


def test_monte_carlo_probability_map_sums_to_100(base_data):
    mc = brs.build_report(base_data)["monte_carlo"]
    total = sum(mc["verdict_probabilities"].values())
    assert abs(total - 100.0) < 0.5


def test_weak_evidence_widens_distribution(base_data):
    import copy
    strong = copy.deepcopy(base_data)
    strong["math"]["13"]["evidence_index"] = 9
    strong["math"]["13"]["statistical_confidence_index"] = 9
    strong["math"]["17"]["fragility_index"] = 1
    weak = copy.deepcopy(base_data)
    weak["math"]["13"]["evidence_index"] = 1
    weak["math"]["13"]["statistical_confidence_index"] = 1
    weak["math"]["17"]["fragility_index"] = 9
    assert brs.uncertainty_sigma(weak) > brs.uncertainty_sigma(strong)


# 10
def test_formula_is_not_arithmetic_mean(base_data):
    # Construct factors with one near-zero factor: an arithmetic mean would stay
    # high, but the weighted geometric mean must collapse.
    data = copy.deepcopy(base_data)
    data["experts"]["09"]["scores"]["legal_safety"] = 5
    data["experts"]["12"]["scores"]["failure_risk"] = 10  # risk_multiplier -> 0.1
    factors = brs.compute_factors(data)
    arithmetic_mean_pct = round(sum(factors.values()) / len(factors) * 100, 1)
    geomean_pct = brs.compute_brs(data, 0.0)
    assert abs(geomean_pct - arithmetic_mean_pct) > 5
    # the near-zero factor must drag geomean well below the arithmetic mean
    assert geomean_pct < arithmetic_mean_pct
