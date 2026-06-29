#!/usr/bin/env bash
# Install biz-eval subagents to Cursor, Claude Code, and Codex agent directories.
#
# Cursor & Claude Code read Markdown subagents with YAML frontmatter.
# Codex reads native TOML subagents (name/description/developer_instructions),
# so for Codex dirs we GENERATE TOML from the same Markdown via build_codex_agents.py.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AGENTS_SRC="$SKILL_DIR/agents"
BUILD_CODEX="$SKILL_DIR/scripts/build_codex_agents.py"
VERIFY="$SKILL_DIR/scripts/verify_subagents.sh"
EXPECTED=18

# Detect project root (where .cursor/, .agents/, etc. should live)
if [ -d "$SKILL_DIR/../../.." ] && [ -d "$SKILL_DIR/../../../.agents" ]; then
  PROJECT_ROOT="$(cd "$SKILL_DIR/../../.." && pwd)"
else
  PROJECT_ROOT="$(pwd)"
fi

cd "$PROJECT_ROOT"
echo "Installing biz-eval subagents"
echo "  project root: $PROJECT_ROOT"
echo "  skill bundle: $SKILL_DIR"
echo ""

install_md() {
  local dest="$1"
  if mkdir -p "$dest" 2>/dev/null; then
    cp -f "$AGENTS_SRC"/*.md "$dest/"
    local n
    n=$(ls "$dest"/biz-eval-*.md 2>/dev/null | wc -l | tr -d ' ')
    if [ "$n" -ne "$EXPECTED" ]; then
      echo "ERROR: $dest has $n agents, expected $EXPECTED" >&2
      return 1
    fi
    echo "Installed $n markdown agents → $dest"
  else
    echo "Skip (not writable): $dest" >&2
    return 1
  fi
}

install_codex() {
  local dest="$1"
  if mkdir -p "$dest" 2>/dev/null; then
    if command -v python3 >/dev/null 2>&1; then
      python3 "$BUILD_CODEX" "$dest"
      local n
      n=$(ls "$dest"/biz-eval-*.toml 2>/dev/null | wc -l | tr -d ' ')
      if [ "$n" -ne "$EXPECTED" ]; then
        echo "ERROR: $dest has $n toml agents, expected $EXPECTED" >&2
        return 1
      fi
    else
      echo "python3 not found; cannot generate Codex TOML for $dest" >&2
      return 1
    fi
  else
    echo "Skip (not writable): $dest" >&2
    return 1
  fi
}

link_skill() {
  local link_path="$1"
  local target="$2"
  local parent
  parent="$(dirname "$link_path")"
  mkdir -p "$parent" 2>/dev/null || return 0
  if [ -L "$link_path" ]; then
    rm -f "$link_path"
  fi
  if [ ! -e "$link_path" ]; then
    ln -sf "$target" "$link_path"
    echo "Linked skill → $link_path"
  fi
}

echo "== Project-level installs =="
install_md ".cursor/agents"
install_md ".claude/agents"
install_md ".agents/agents"
install_codex ".codex/agents"

echo ""
echo "== Skill discovery symlinks =="
# Relative symlinks from project root
link_skill ".cursor/skills/business-idea-evaluator" ".agents/skills/business-idea-evaluator"
link_skill ".claude/skills/business-idea-evaluator" ".agents/skills/business-idea-evaluator"

echo ""
echo "== User-level installs (all projects) =="
install_md "$HOME/.cursor/agents" || true
install_md "$HOME/.claude/agents" || true
install_codex "$HOME/.codex/agents" || true

echo ""
echo "== Verification =="
bash "$VERIFY" "$PROJECT_ROOT"

echo ""
echo "Done. Subagents prefixed biz-eval-* are ready for Cursor, Claude Code, and Codex."
