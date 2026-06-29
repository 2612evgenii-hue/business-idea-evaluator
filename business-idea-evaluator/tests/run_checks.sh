#!/usr/bin/env bash
# Reproducible verification for business-idea-evaluator.
# Run from the skill root:  bash tests/run_checks.sh
set -euo pipefail

cd "$(dirname "$0")/.."
fail=0

echo "== 1. Python syntax (calculate_brs.py) =="
python3 -m py_compile scripts/calculate_brs.py && echo "PASS"

echo "== 2. Python syntax (validators + codex builder) =="
python3 -m py_compile scripts/validate_evidence_package.py scripts/validate_input.py scripts/build_codex_agents.py && echo "PASS"

echo "== 3. Bash syntax (install-agents.sh) =="
bash -n scripts/install-agents.sh && echo "PASS"

echo "== 4. Evidence package validation (example) =="
python3 scripts/validate_evidence_package.py references/example-input.json >/dev/null && echo "PASS"

echo "== 5. BRS computation (example) =="
python3 scripts/calculate_brs.py references/example-input.json \
  | python3 -c "import sys,json; b=json.load(sys.stdin)['business_reality_score']; print(f\"BRS base={b['base']} range={b['min']}-{b['max']} verdict={b['verdict_code']}\")"

echo "== 6. All 18 subagents present =="
n=$(ls agents/biz-eval-*.md | wc -l | tr -d ' ')
echo "found $n agent files"
[ "$n" -eq 18 ] && echo "PASS" || { echo "FAIL: expected 18"; fail=1; }

echo "== 7. Frontmatter sanity (each agent starts with --- and has name:) =="
for f in agents/biz-eval-*.md; do
  head -1 "$f" | grep -q '^---$' || { echo "FAIL $f: no opening ---"; fail=1; }
  grep -q '^name: biz-eval-' "$f" || { echo "FAIL $f: no name field"; fail=1; }
done
[ "$fail" -eq 0 ] && echo "PASS"

echo "== 8. Codex TOML generation (18 agents) =="
tmp=$(mktemp -d)
python3 scripts/build_codex_agents.py "$tmp" >/dev/null
nt=$(ls "$tmp"/biz-eval-*.toml | wc -l | tr -d ' ')
rm -rf "$tmp"
[ "$nt" -eq 18 ] && echo "PASS ($nt toml)" || { echo "FAIL: expected 18 toml"; fail=1; }

echo "== 9. Risk-direction regression =="
python3 - <<'PY'
import json, subprocess, tempfile, os
base = json.load(open("references/example-input.json"))
def rm(legal_safety, failure_risk):
    d = json.loads(json.dumps(base))
    d["experts"]["09"]["scores"]["legal_safety"] = legal_safety
    d["experts"]["09"]["scores"]["platform_stability"] = 8
    d["experts"]["12"]["scores"]["failure_risk"] = failure_risk
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False); json.dump(d, f); f.close()
    out = json.loads(subprocess.check_output(["python3", "scripts/calculate_brs.py", f.name])); os.unlink(f.name)
    return out["factors"]["risk_multiplier"]
safe, risky, unsafe = rm(9, 2), rm(9, 9), rm(2, 2)
assert risky < safe, "high failure_risk must lower risk_multiplier"
assert unsafe < safe, "low legal_safety must lower risk_multiplier"
print(f"safe={safe:.2f} risky={risky:.2f} unsafe={unsafe:.2f}  PASS")
PY

echo "== 10. Blocking cap (legal_safety=2 -> cap 35) =="
python3 - <<'PY'
import json, subprocess, tempfile, os
d = json.load(open("references/example-input.json"))
d["experts"]["09"]["scores"]["legal_safety"] = 2
f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False); json.dump(d, f); f.close()
o = json.loads(subprocess.check_output(["python3", "scripts/calculate_brs.py", f.name])); os.unlink(f.name)
assert o["business_reality_score"]["base"] <= 35, "cap not applied"
print("cap applied, base =", o["business_reality_score"]["base"], " PASS")
PY

echo "== 11. Calibration corpus (known ideas) =="
python3 scripts/run_calibration.py | tail -2

echo "== 12. pytest suite =="
if command -v pytest >/dev/null 2>&1; then
  pytest -q && echo "PASS"
else
  python3 -m pytest -q && echo "PASS"
fi

[ "$fail" -eq 0 ] && echo "ALL CHECKS PASSED" || { echo "SOME CHECKS FAILED"; exit 1; }
