#!/usr/bin/env python3
"""Convert Agent-Skills Markdown subagents (agents/*.md) into native Codex TOML.

Codex custom subagents are standalone TOML files in `.codex/agents/` with the
required fields `name`, `description`, `developer_instructions`. This script
generates those TOML files from the canonical Markdown definitions so the same
18 subagents work natively in Codex — real compatibility, not a copy of .md.

Usage:
    python3 build_codex_agents.py [DEST_DIR]      # default: .codex/agents
"""

from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
AGENTS_SRC = SKILL_ROOT / "agents"


def parse_agent(md: str) -> tuple[dict[str, str], str]:
    """Return (frontmatter dict, body)."""
    fm: dict[str, str] = {}
    body = md
    if md.startswith("---"):
        end = md.find("\n---", 3)
        if end != -1:
            block = md[3:end].strip("\n")
            body = md[end + 4 :].lstrip("\n")
            for line in block.splitlines():
                if ":" in line:
                    key, _, val = line.partition(":")
                    fm[key.strip()] = val.strip()
    return fm, body


def toml_literal(value: str) -> str:
    """TOML multiline literal string (no escape processing). Strip stray '''."""
    return "'''\n" + value.replace("'''", "''") + "\n'''"


def to_toml(fm: dict[str, str], body: str) -> str:
    name = fm.get("name", "unnamed-agent")
    description = fm.get("description", "").replace('"', "'")
    readonly = fm.get("readonly", "false").lower() == "true"
    lines = [
        f'name = "{name}"',
        f'description = "{description}"',
    ]
    if readonly:
        lines.append('sandbox_mode = "read-only"')
    lines.append(f"developer_instructions = {toml_literal(body.strip())}")
    return "\n".join(lines) + "\n"


def main() -> None:
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".codex/agents")
    dest.mkdir(parents=True, exist_ok=True)

    md_files = sorted(AGENTS_SRC.glob("biz-eval-*.md"))
    if not md_files:
        print(f"No agent markdown found in {AGENTS_SRC}", file=sys.stderr)
        sys.exit(1)

    count = 0
    for md_path in md_files:
        fm, body = parse_agent(md_path.read_text(encoding="utf-8"))
        toml = to_toml(fm, body)
        out_path = dest / (md_path.stem + ".toml")
        out_path.write_text(toml, encoding="utf-8")
        count += 1

    print(f"Generated {count} Codex TOML subagents → {dest}")


if __name__ == "__main__":
    main()
