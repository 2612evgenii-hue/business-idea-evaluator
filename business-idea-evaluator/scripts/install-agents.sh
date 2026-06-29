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

install_md() {
  local dest="$1"
  if mkdir -p "$dest" 2>/dev/null; then
    cp -f "$AGENTS_SRC"/*.md "$dest/"
    echo "Installed $(ls "$AGENTS_SRC"/*.md | wc -l | tr -d ' ') markdown agents → $dest"
  else
    echo "Skip (not writable): $dest"
  fi
}

install_codex() {
  local dest="$1"
  if mkdir -p "$dest" 2>/dev/null; then
    if command -v python3 >/dev/null 2>&1; then
      python3 "$BUILD_CODEX" "$dest"
    else
      echo "python3 not found; copying markdown to $dest instead"
      cp -f "$AGENTS_SRC"/*.md "$dest/"
    fi
  else
    echo "Skip (not writable): $dest"
  fi
}

# Project-level (relative to cwd when user runs from repo root)
install_md ".cursor/agents"
install_md ".claude/agents"
install_md ".agents/agents"
install_codex ".codex/agents"

# User-level
install_md "$HOME/.cursor/agents"
install_md "$HOME/.claude/agents"
install_codex "$HOME/.codex/agents"

echo "Done. Subagents prefixed biz-eval-*"
