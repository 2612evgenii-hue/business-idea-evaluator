"""Tests for subagent installation and verification scripts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_ROOT / "scripts"
AGENTS_SRC = SKILL_ROOT / "agents"


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd or SKILL_ROOT, capture_output=True, text=True, check=False)


def test_source_bundle_has_18_agents():
    files = sorted(AGENTS_SRC.glob("biz-eval-*.md"))
    assert len(files) == 18, f"expected 18 agent files, got {len(files)}"


def test_each_agent_name_matches_filename():
    for path in sorted(AGENTS_SRC.glob("biz-eval-*.md")):
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---"), f"{path.name}: missing frontmatter"
        name_line = next((l for l in text.splitlines() if l.startswith("name:")), None)
        assert name_line, f"{path.name}: missing name field"
        declared = name_line.split(":", 1)[1].strip()
        assert declared == path.stem, f"{path.name}: name={declared!r} != {path.stem!r}"


def test_codex_toml_generation_has_required_fields(tmp_path):
    dest = tmp_path / "codex"
    dest.mkdir()
    proc = run([sys.executable, str(SCRIPTS / "build_codex_agents.py"), str(dest)])
    assert proc.returncode == 0, proc.stderr
    toml_files = sorted(dest.glob("biz-eval-*.toml"))
    assert len(toml_files) == 18
    for tf in toml_files:
        content = tf.read_text(encoding="utf-8")
        assert 'name = "biz-eval-' in content
        assert "description = " in content
        assert "developer_instructions = " in content


def test_verify_script_exits_zero_on_installed_project():
    project_root = SKILL_ROOT.parent.parent.parent  # .agents/skills/bie -> test root
    verify = SCRIPTS / "verify_subagents.sh"
    if not (project_root / "AGENTS.md").is_file():
        return  # skip when not in full project layout
    proc = run(["bash", str(verify), str(project_root)])
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_install_script_bash_syntax():
    proc = run(["bash", "-n", str(SCRIPTS / "install-agents.sh")])
    assert proc.returncode == 0
