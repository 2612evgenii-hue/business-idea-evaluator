#!/usr/bin/env bash
# Install biz-eval subagents to Cursor, Claude Code, and Codex agent directories.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AGENTS_SRC="$SKILL_DIR/agents"

install_dir() {
  local dest="$1"
  if mkdir -p "$dest" 2>/dev/null; then
    cp -f "$AGENTS_SRC"/*.md "$dest/"
    echo "Installed $(ls "$AGENTS_SRC"/*.md | wc -l | tr -d ' ') agents → $dest"
  else
    echo "Skip (not writable): $dest"
  fi
}

# Project-level (relative to cwd when user runs from repo root)
install_dir ".cursor/agents"
install_dir ".claude/agents"
install_dir ".codex/agents"
install_dir ".agents/agents"

# User-level
install_dir "$HOME/.cursor/agents"
install_dir "$HOME/.claude/agents"
install_dir "$HOME/.codex/agents"

echo "Done. Subagents prefixed biz-eval-*"
