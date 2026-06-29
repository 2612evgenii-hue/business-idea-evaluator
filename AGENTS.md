# AGENTS.md — Business Idea Evaluator

Project guidance for agentic tools (Codex reads this file automatically; Claude Code and Cursor also honor it).

## What this repo is

A cross-platform Agent Skill that evaluates business ideas objectively through 18 subagents and a deterministic Business Reality Score (BRS). The skill lives in `business-idea-evaluator/`.

## How to run the evaluation

1. Activate the skill `business-idea-evaluator` (see `business-idea-evaluator/SKILL.md`).
2. Phase 1: ask exactly 5 dependent clarifying questions, one per message; confirm the idea.
3. Phase 2: launch all 12 expert subagents (`business-idea-evaluator/agents/biz-eval-01..12`).
4. Phase 3: launch all 6 math subagents (`biz-eval-13..18`).
5. Phase 4: validate then score:

```bash
python3 business-idea-evaluator/scripts/validate_evidence_package.py biz-eval-input.json
python3 business-idea-evaluator/scripts/calculate_brs.py biz-eval-input.json
```

6. Phase 5: render the final report (`business-idea-evaluator/references/report-template.md`).

## Hard rules

- Never evaluate before the idea is confirmed.
- Never use arithmetic mean for the final score — only `calculate_brs.py` (weighted geometric mean + blocking caps).
- Never flatter; see `business-idea-evaluator/references/forbidden-phrases.md`.
- If web search is unavailable, mark market claims as hypotheses and cap source quality.

## Codex note on subagents

Codex custom subagents are native TOML in `.codex/agents/` with required fields
`name`, `description`, `developer_instructions`. This skill keeps the canonical
subagents as Agent-Skills Markdown (`agents/*.md`) and **generates** the Codex TOML
from them via `scripts/build_codex_agents.py`. `install-agents.sh` calls this
automatically for any `.codex/agents` directory, so Codex gets real native TOML
subagents (not a copy of Markdown). To regenerate manually:

```bash
python3 business-idea-evaluator/scripts/build_codex_agents.py .codex/agents
```

Subagents are spawned per phase (12 expert, then 6 math). Prompt Codex explicitly
to "spawn N agents in parallel" — Codex does not auto-spawn subagents.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/validate_evidence_package.py` | Validate merged input JSON (+ JSON Schema if `jsonschema` installed) |
| `scripts/validate_input.py` | Backward-compatible alias for the validator |
| `scripts/calculate_brs.py` | Authoritative BRS computation |
| `scripts/build_codex_agents.py` | Generate native Codex TOML subagents from Markdown |
| `scripts/install-agents.sh` | Install 18 subagents into Cursor/Claude (MD) and Codex (TOML) dirs |
