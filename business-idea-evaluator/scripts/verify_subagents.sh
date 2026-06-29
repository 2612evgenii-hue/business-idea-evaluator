#!/usr/bin/env bash
# Verify biz-eval subagents are installed for Cursor, Claude Code, and Codex.
# Usage:
#   bash scripts/verify_subagents.sh              # from project root
#   bash scripts/verify_subagents.sh /path/to/project
#   bash scripts/verify_subagents.sh --strict     # fail if user-level dirs missing
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AGENTS_SRC="$SKILL_DIR/agents"
EXPECTED=18
STRICT=0
PROJECT_ROOT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --strict) STRICT=1; shift ;;
    -*) echo "Unknown option: $1" >&2; exit 2 ;;
    *) PROJECT_ROOT="$1"; shift ;;
  esac
done

if [ -z "$PROJECT_ROOT" ]; then
  if [ -d "$SKILL_DIR/../../.." ] && [ -d "$SKILL_DIR/../../../.agents/skills" ]; then
    PROJECT_ROOT="$(cd "$SKILL_DIR/../../.." && pwd)"
  else
    PROJECT_ROOT="$(pwd)"
  fi
fi

PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
FAIL=0

echo "Verifying biz-eval subagents"
echo "  project root: $PROJECT_ROOT"
echo "  skill source: $AGENTS_SRC"
echo "  expected:     $EXPECTED agents per platform dir"
echo ""

# Canonical list from source bundle (bash 3.2 compatible — no mapfile)
CANONICAL=()
while IFS= read -r line; do
  CANONICAL+=("$line")
done <<EOF
$(cd "$AGENTS_SRC" && ls biz-eval-*.md | sort)
EOF

check_md_dir() {
  local dir="$1"
  local label="$2"
  local required="${3:-1}"

  if [ ! -d "$dir" ]; then
    if [ "$required" -eq 1 ]; then
      echo "FAIL  $label: directory missing → $dir"
      FAIL=1
    else
      echo "SKIP  $label: not present (optional) → $dir"
    fi
    return
  fi

  local missing=0
  local wrong_name=0
  for base in "${CANONICAL[@]}"; do
    local f="$dir/$base"
    if [ ! -f "$f" ]; then
      echo "FAIL  $label: missing $base"
      missing=$((missing + 1))
      FAIL=1
      continue
    fi
    local declared
    declared=$(grep '^name:' "$f" | head -1 | sed 's/^name:[[:space:]]*//')
    local expected="${base%.md}"
    if [ "$declared" != "$expected" ]; then
      echo "FAIL  $label: $base has name='$declared' (expected '$expected')"
      wrong_name=$((wrong_name + 1))
      FAIL=1
    fi
  done

  local count
  count=$(ls "$dir"/biz-eval-*.md 2>/dev/null | wc -l | tr -d ' ')
  if [ "$missing" -eq 0 ] && [ "$wrong_name" -eq 0 ] && [ "$count" -eq "$EXPECTED" ]; then
    echo "OK    $label: $count/$EXPECTED markdown agents → $dir"
  elif [ "$count" -ne "$EXPECTED" ]; then
    echo "FAIL  $label: $count/$EXPECTED agents → $dir"
    FAIL=1
  fi
}

check_toml_dir() {
  local dir="$1"
  local label="$2"
  local required="${3:-1}"

  if [ ! -d "$dir" ]; then
    if [ "$required" -eq 1 ]; then
      echo "FAIL  $label: directory missing → $dir"
      FAIL=1
    else
      echo "SKIP  $label: not present (optional) → $dir"
    fi
    return
  fi

  local bad=0
  for base in "${CANONICAL[@]}"; do
    local stem="${base%.md}"
    local f="$dir/${stem}.toml"
    if [ ! -f "$f" ]; then
      echo "FAIL  $label: missing ${stem}.toml"
      bad=$((bad + 1))
      FAIL=1
      continue
    fi
    if ! grep -q '^name = "biz-eval-' "$f"; then
      echo "FAIL  $label: ${stem}.toml missing name field"
      bad=$((bad + 1))
      FAIL=1
    fi
    if ! grep -q '^description = ' "$f"; then
      echo "FAIL  $label: ${stem}.toml missing description"
      bad=$((bad + 1))
      FAIL=1
    fi
    if ! grep -q '^developer_instructions = ' "$f"; then
      echo "FAIL  $label: ${stem}.toml missing developer_instructions"
      bad=$((bad + 1))
      FAIL=1
    fi
  done

  local count
  count=$(ls "$dir"/biz-eval-*.toml 2>/dev/null | wc -l | tr -d ' ')
  if [ "$bad" -eq 0 ] && [ "$count" -eq "$EXPECTED" ]; then
    echo "OK    $label: $count/$EXPECTED Codex TOML agents → $dir"
  elif [ "$count" -ne "$EXPECTED" ]; then
    echo "FAIL  $label: $count/$EXPECTED toml files → $dir"
    FAIL=1
  fi
}

check_skill_links() {
  local link="$1"
  local label="$2"
  if [ -L "$link" ] || [ -d "$link" ]; then
    echo "OK    $label: $link"
  else
    echo "WARN  $label: missing skill link → $link (optional; .agents/skills/ still works)"
  fi
}

echo "== Project-level (required) =="
check_md_dir "$PROJECT_ROOT/.cursor/agents" "Cursor agents" 1
check_md_dir "$PROJECT_ROOT/.claude/agents" "Claude Code agents" 1
check_md_dir "$PROJECT_ROOT/.agents/agents" "Shared .agents/agents" 1
check_toml_dir "$PROJECT_ROOT/.codex/agents" "Codex agents" 1

echo ""
echo "== Skill discovery paths =="
check_skill_links "$PROJECT_ROOT/.agents/skills/business-idea-evaluator" "Skill bundle"
check_skill_links "$PROJECT_ROOT/.cursor/skills/business-idea-evaluator" "Cursor skills symlink"
check_skill_links "$PROJECT_ROOT/.claude/skills/business-idea-evaluator" "Claude skills symlink"

if [ -f "$PROJECT_ROOT/.cursor/rules/business-idea-evaluator.mdc" ]; then
  echo "OK    Cursor rule: .cursor/rules/business-idea-evaluator.mdc"
else
  echo "FAIL  Cursor rule missing: .cursor/rules/business-idea-evaluator.mdc"
  FAIL=1
fi

if [ -f "$PROJECT_ROOT/AGENTS.md" ]; then
  echo "OK    AGENTS.md at project root"
else
  echo "FAIL  AGENTS.md missing at project root"
  FAIL=1
fi

echo ""
echo "== User-level (optional) =="
check_md_dir "$HOME/.cursor/agents" "Cursor user agents" "$STRICT"
check_md_dir "$HOME/.claude/agents" "Claude user agents" "$STRICT"
check_toml_dir "$HOME/.codex/agents" "Codex user agents" "$STRICT"

echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "VERIFY PASSED — all required subagent directories are complete."
  exit 0
else
  echo "VERIFY FAILED — run: bash $SKILL_DIR/scripts/install-agents.sh"
  exit 1
fi
