# AGENTS.md — Business Idea Evaluator

Project guidance for agentic tools (Codex reads this file automatically; Claude Code and Cursor also honor it).

## What this project provides

A cross-platform Agent Skill that evaluates business ideas objectively through **18 real subagents** and a deterministic **Business Reality Score (BRS)**.

- Skill orchestrator: `.agents/skills/business-idea-evaluator/SKILL.md`
- Subagent definitions: `.agents/skills/business-idea-evaluator/agents/biz-eval-*.md`

## First-time setup (required)

Run once from project root:

```bash
bash .agents/skills/business-idea-evaluator/scripts/bootstrap.sh
```

This installs 18 subagents into platform directories and runs the quality gate.

Or step by step:

```bash
bash .agents/skills/business-idea-evaluator/scripts/install-agents.sh
bash .agents/skills/business-idea-evaluator/scripts/verify_subagents.sh
```

### Where subagents are installed

| Platform | Agents directory | Format |
|----------|----------------|--------|
| **Cursor** | `.cursor/agents/` | Markdown + YAML frontmatter |
| **Claude Code** | `.claude/agents/` | Markdown + YAML frontmatter |
| **Codex** | `.codex/agents/` | Native TOML (generated from Markdown) |
| **Shared** | `.agents/agents/` | Markdown (fallback) |

Skill discovery paths (symlinks created by installer):

- `.agents/skills/business-idea-evaluator/` — canonical bundle
- `.cursor/skills/business-idea-evaluator` → symlink
- `.claude/skills/business-idea-evaluator` → symlink

## How to run the evaluation

1. Activate skill `business-idea-evaluator` (auto-triggered on "оцени бизнес-идею" etc.).
2. **Phase 1:** Ask exactly 5 dependent clarifying questions, one per message; confirm the idea.
3. **Phase 2:** Launch all **12 expert** subagents in parallel via Task/Agent tool (`biz-eval-01` … `biz-eval-12`). **Never simulate in main context.**
4. **Phase 3:** Launch all **6 math** subagents in parallel (`biz-eval-13` … `biz-eval-18`).
5. **Phase 4:** Validate and score:

```bash
python3 .agents/skills/business-idea-evaluator/scripts/validate_evidence_package.py biz-eval-input.json
python3 .agents/skills/business-idea-evaluator/scripts/calculate_brs.py biz-eval-input.json
```

6. **Phase 5:** Render the final report (`.agents/skills/business-idea-evaluator/references/report-template.md`).

## Hard rules

- **Never evaluate before the idea is confirmed** (Phase 1 gate).
- **Never simulate subagents** — each of 18 must be a separate Task/Agent invocation with its own context.
- **Never use arithmetic mean** for the final score — only `calculate_brs.py`.
- **Never flatter** — see `references/forbidden-phrases.md`.
- If web search is unavailable, mark market claims as hypotheses and cap source quality.

## Pre-flight before Phase 2

```bash
bash .agents/skills/business-idea-evaluator/scripts/verify_subagents.sh
```

If verification fails, run `install-agents.sh` first. Do not proceed to expert layer without 18 installed subagents.

## Codex note

Codex custom subagents are native TOML in `.codex/agents/`. The installer generates them via `build_codex_agents.py`. Prompt Codex explicitly: *"spawn 12 expert agents in parallel"*, then *"spawn 6 math agents in parallel"* — Codex does not auto-spawn.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/bootstrap.sh` | Install + verify + quality gate (one command) |
| `scripts/install-agents.sh` | Install 18 subagents to all platform dirs |
| `scripts/verify_subagents.sh` | Verify subagents exist and are valid |
| `scripts/validate_evidence_package.py` | Validate merged input JSON |
| `scripts/calculate_brs.py` | Authoritative BRS computation |
| `scripts/build_codex_agents.py` | Generate Codex TOML from Markdown |
| `tests/run_checks.sh` | Full quality gate |
