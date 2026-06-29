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
python3 business-idea-evaluator/scripts/validate_input.py biz-eval-input.json
python3 business-idea-evaluator/scripts/calculate_brs.py biz-eval-input.json
```

6. Phase 5: render the final report (`business-idea-evaluator/references/report-template.md`).

## Hard rules

- Never evaluate before the idea is confirmed.
- Never use arithmetic mean for the final score — only `calculate_brs.py` (geometric mean + blocking caps).
- Never flatter; see `business-idea-evaluator/references/forbidden-phrases.md`.
- If web search is unavailable, mark market claims as hypotheses and cap source quality.

## Codex note on subagents

Codex custom subagents are typically TOML in `.codex/agents/`. This skill ships subagents as
Agent-Skills-standard Markdown (`agents/*.md` with YAML frontmatter: `name`, `description`,
`model`, `readonly`). In Codex these files are read as the role definitions the orchestrator
applies per phase. If your Codex version requires native TOML subagents, the same `name` +
instruction body map directly to `name` + `developer_instructions`.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/validate_input.py` | Validate merged input JSON before scoring |
| `scripts/calculate_brs.py` | Authoritative BRS computation |
| `scripts/install-agents.sh` | Copy 18 subagents into platform agent dirs |
