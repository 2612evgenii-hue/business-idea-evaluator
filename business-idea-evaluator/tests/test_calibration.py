"""Calibration tests: the formula must not over-rate failures or kill successes.

Runs the known-idea corpus in calibration_cases/ and asserts the aggregate
sanity properties. Guards the scoring math against silent regressions.
"""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import run_calibration as cal  # noqa: E402


def test_corpus_size():
    results = cal.evaluate_cases()
    assert len(results) >= 10, "calibration corpus should have >= 10 cases"


def test_all_brs_in_bounds():
    for r in cal.evaluate_cases():
        assert 0 <= r["brs"] <= 100


def test_aggregate_sanity():
    results = cal.evaluate_cases()
    ok, msgs = cal.aggregate_checks(results)
    assert ok, "calibration failed:\n" + "\n".join(msgs)


def test_success_beats_failure_separation():
    results = cal.evaluate_cases()
    succ = [r["brs"] for r in results if r["outcome"] == "success"]
    fail = [r["brs"] for r in results if r["outcome"] == "failure"]
    assert min(succ) > max(fail), "successes and failures must be clearly separated"


def test_legal_failure_is_capped():
    # Theranos has blocking legal risk -> must be in the lowest bands.
    results = {r["file"]: r for r in cal.evaluate_cases()}
    theranos = results["failure-theranos.json"]
    assert theranos["brs"] <= 25
