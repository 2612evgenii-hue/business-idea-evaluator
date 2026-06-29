#!/usr/bin/env bash
# One-command setup: install subagents + verify + run quality gate.
# Run from anywhere; detects project root automatically.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Business Idea Evaluator — bootstrap ==="
echo ""

bash "$SKILL_DIR/scripts/install-agents.sh"
echo ""
bash "$SKILL_DIR/tests/run_checks.sh"

echo ""
echo "Bootstrap complete. Skill is ready for Cursor, Claude Code, and Codex."
