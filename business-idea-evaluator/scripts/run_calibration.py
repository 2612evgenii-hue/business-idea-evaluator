#!/usr/bin/env python3
"""Calibration harness for the BRS model.

Runs calculate_brs on a corpus of known real-world ideas (success / failure /
mixed) and checks the formula does not over-rate clear failures or kill clear
successes. This is the guardrail against silent regressions in the scoring math.

Usage:
    python3 run_calibration.py [calibration_cases_dir]
Exit codes: 0 = all sanity checks pass, 1 = a sanity check failed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPTS.parent
DEFAULT_CASES = SKILL_ROOT / "calibration_cases"

sys.path.insert(0, str(SCRIPTS))

import calculate_brs as brs  # noqa: E402

# Verdict bands ranked low -> high.
BAND_RANK = {
    "DO_NOT_LAUNCH": 0,
    "CHEAP_TESTS_ONLY": 1,
    "REFORMULATE": 2,
    "TEST_NARROW_SEGMENT": 3,
}


def evaluate_cases(cases_dir: Path = DEFAULT_CASES) -> list[dict]:
    results: list[dict] = []
    for path in sorted(cases_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        meta = data.get("calibration", {})
        # Fixed seed for reproducible calibration.
        report = brs.build_report(data, simulations=1500, seed=7)
        s = report["business_reality_score"]
        results.append({
            "file": path.name,
            "name": meta.get("name", path.stem),
            "outcome": meta.get("real_world_outcome", "unknown"),
            "brs": s["base"],
            "verdict": s["verdict_code"],
            "mc_p50": report["monte_carlo"]["brs_p50"],
        })
    return results


def aggregate_checks(results: list[dict]) -> tuple[bool, list[str]]:
    """Return (ok, messages). Sanity properties a sound model must satisfy."""
    msgs: list[str] = []
    ok = True

    def mean(outcome: str) -> float:
        xs = [r["brs"] for r in results if r["outcome"] == outcome]
        return sum(xs) / len(xs) if xs else 0.0

    s_mean, m_mean, f_mean = mean("success"), mean("mixed"), mean("failure")
    msgs.append(f"mean BRS: success={s_mean:.1f} mixed={m_mean:.1f} failure={f_mean:.1f}")

    if not (s_mean > m_mean > f_mean):
        ok = False
        msgs.append("FAIL: expected success > mixed > failure mean BRS")

    # No clear failure may land in the strongest band.
    for r in results:
        if r["outcome"] == "failure" and BAND_RANK[r["verdict"]] >= BAND_RANK["TEST_NARROW_SEGMENT"]:
            ok = False
            msgs.append(f"FAIL: failure '{r['name']}' scored TEST_NARROW ({r['brs']})")
        if r["outcome"] == "success" and BAND_RANK[r["verdict"]] <= BAND_RANK["DO_NOT_LAUNCH"]:
            ok = False
            msgs.append(f"FAIL: success '{r['name']}' scored DO_NOT_LAUNCH ({r['brs']})")

    # Clear separation: best failure should not beat worst success.
    succ = [r["brs"] for r in results if r["outcome"] == "success"]
    fail = [r["brs"] for r in results if r["outcome"] == "failure"]
    if succ and fail and min(succ) <= max(fail):
        ok = False
        msgs.append(f"FAIL: worst success ({min(succ)}) <= best failure ({max(fail)})")

    return ok, msgs


def main() -> None:
    cases_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CASES
    results = evaluate_cases(cases_dir)

    width = max(len(r["name"]) for r in results)
    print(f"{'CASE'.ljust(width)}  OUTCOME    BRS   VERDICT")
    print("-" * (width + 30))
    for r in sorted(results, key=lambda x: (-x["brs"])):
        print(f"{r['name'].ljust(width)}  {r['outcome'].ljust(9)}  {r['brs']:>4}  {r['verdict']}")

    ok, msgs = aggregate_checks(results)
    print()
    for m in msgs:
        print(m)
    print("\nCALIBRATION " + ("PASSED" if ok else "FAILED"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
