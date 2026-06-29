---
name: business-idea-evaluator
description: >
  Objectively evaluates business ideas through 18 independent subagents, evidence
  grading, probabilistic modeling, and Business Reality Score (BRS). Use when the
  user asks to evaluate, validate, score, or stress-test a business idea, startup
  concept, side project, SaaS idea, or monetization plan. Always use for business
  idea analysis — never evaluate from gut feeling in main context. Requires real
  subagent invocation, not simulated expert opinions.
disable-model-invocation: false
---

# Business Idea Evaluator

Professional analytical system. **Not** a motivational coach. Evaluate the idea, not the user's enthusiasm.

## Non-negotiable rules

1. **Never evaluate before idea is confirmed** — complete Phase 1 first.
2. **Never simulate subagents in main context** — launch all 18 via Task/Agent tool.
3. **Never use simple arithmetic mean** for final score — use `scripts/calculate_brs.py`.
4. **Never flatter** — see [references/forbidden-phrases.md](references/forbidden-phrases.md).
5. **Never claim "no competitors"** without expert 01 completing deep search.
6. **Mark evidence status** on every material claim — see [references/evidence-status.md](references/evidence-status.md).
7. If web search unavailable, state it once and downgrade all market claims to hypotheses.

## Phase 1 — Idea discovery (5 questions)

See [references/discovery-protocol.md](references/discovery-protocol.md) for slot map and examples.

Ask **exactly one question per message**. Wait for answer before next question.

| # | Goal | First question depends on |
|---|------|---------------------------|
| 1 | Who is the paying customer | Your reading of user's initial idea |
| 2 | Specific pain + frequency | Answer to Q1 |
| 3 | Current workaround + cost of pain | Answer to Q2 |
| 4 | Product format + what customer pays for | Answer to Q3 |
| 5 | Launch market + MVP constraints | Answer to Q4 |

Rules for questions:
- Max 2 sentences per question.
- No "tell me more" or open-ended prompts.
- Each question must extract one concrete business-model element.
- Track answers internally; do not dump full Q&A into final report.

After Q5, output **only**:

```
Я понял идею так: [one dense paragraph covering: audience, pain, solution,
delivery format, monetization, launch market, differentiation, first MVP]
```

Then ask: **«Подтверждаешь такую формулировку или нужно поправить?»**

- If user corrects → update paragraph, ask confirmation again.
- **Do not proceed to Phase 2 until explicit confirmation** («да», «подтверждаю», «верно», etc.).

Save confirmed idea as `IDEA_BRIEF` for all subagents.

## Phase 2 — Expert layer (12 subagents)

Launch **all 12 in parallel** (one message, 12 Task/Agent invocations). Read [references/expert-evidence-package.md](references/expert-evidence-package.md) for output schema.

| Agent file | Role |
|------------|------|
| `biz-eval-01-analog-research` | Deep analog & substitute search |
| `biz-eval-02-pain-demand` | Real pain & willingness to pay |
| `biz-eval-03-audience-behavior` | Buyer behavior & acquisition |
| `biz-eval-04-market-country` | Country/market realities |
| `biz-eval-05-trends-longevity` | Trend & 1–5y durability |
| `biz-eval-06-monetization` | Revenue model & unit economics hints |
| `biz-eval-07-marketing` | Channels & trust barriers |
| `biz-eval-08-implementation` | MVP & technical feasibility |
| `biz-eval-09-legal-platform` | Legal/platform/ethical risks |
| `biz-eval-10-competitive-moat` | Copyability & defensibility |
| `biz-eval-11-launch-zero` | 7/30/90 day launch plan |
| `biz-eval-12-red-team` | Attack the idea |

**Install agents if missing:** run `bash scripts/install-agents.sh` from skill root.

### Prompt template for each expert

```text
IDEA_BRIEF:
<paste confirmed paragraph>

TASK: Execute your role per agent definition. Use web search if available.
Return ONLY valid JSON matching the schema in references/expert-evidence-package.md
for your agent_id. Include sources with URLs when found.
```

Collect all 12 JSON outputs. Merge into `Expert Evidence Package` (single JSON file or structured object). Write to `biz-eval-evidence.json` in workspace temp if needed.

**Gate:** Do not start Phase 3 until all 12 expert JSONs are received. If one fails, retry once; if still failing, note `agent_failed` in package and continue with penalty.

## Phase 3 — Math layer (6 subagents)

Launch **all 6 in parallel** after Expert Evidence Package is complete. Each math
subagent receives the **full** Expert Evidence Package and works **independently**
of the other math subagents — it does not re-research the market, it processes the
package numerically (counts, ranges, penalties). Independence is enforced by giving
each its own context (separate Task/Agent invocation), not by prompt wording.

| Agent | Input | Role |
|-------|-------|------|
| `biz-eval-13-evidence-stats` | Full package | Evidence & source quality indices |
| `biz-eval-14-math-model` | Package + agent 13 | Formula design & variable weights |
| `biz-eval-15-scenario-probability` | Full package | 4-scenario probability map |
| `biz-eval-16-unit-economics` | Full package | CAC/LTV/churn model |
| `biz-eval-17-sensitivity` | Full package | Top sensitivity parameters |
| `biz-eval-18-experiments` | Full package + math outputs | Validation experiments |

### Prompt template for math agents

```text
EXPERT_EVIDENCE_PACKAGE:
<paste full JSON from Phase 2>

TASK: Execute your role. Return ONLY valid JSON per your agent schema.
Do not re-research market — process the package mathematically.
```

## Phase 4 — Deterministic BRS calculation

1. Merge expert scores + math agent outputs into `biz-eval-input.json` (see [references/scoring-formula.md](references/scoring-formula.md); structure defined in [references/evidence-package.schema.json](references/evidence-package.schema.json)).
2. Validate, then score:

```bash
python3 scripts/validate_evidence_package.py biz-eval-input.json
python3 scripts/calculate_brs.py biz-eval-input.json
```

3. Use script output as **authoritative** Business Reality Score. Main agent explains results; does not override numbers.

The script returns: `base/min/max` BRS, `confidence`, `evidence_index`,
`source_quality_index`, `hypothetical` flag, `blocking_caps_applied`,
`main_blocking_risk`, `main_growth_factor`, `main_uncertainty_factor`, the nine
`factors`, a `monte_carlo` block (BRS distribution from seeded simulations whose
spread is driven by the evidence base), a computed `probability_map` (verdict-band
probabilities), and input `warnings`. Tune runs with `--simulations N --seed N`.

A worked input/output pair lives in `references/example-input.json` and
`references/example-output.json` (also `examples/sample-input.json`).

If script fails, fix JSON and retry. Do not invent score manually.

## Phase 5 — Final report

Render using [references/report-template.md](references/report-template.md).

Verdict must map to BRS:
- **≥65** — test in narrow segment (not "launch fully")
- **45–64** — change model or segment before spending
- **25–44** — weak; only cheap experiments justified
- **<25** — do not launch in current form

Always separate: proven by sources | statistical | hypothesis | needs verification.

## Subagent installation

Agents live in skill bundle at `agents/`. Install to platform dirs:

```bash
bash .agents/skills/business-idea-evaluator/scripts/install-agents.sh
```

Targets (when writable): `.cursor/agents/`, `.claude/agents/`, `.agents/agents/` get
Markdown; `.codex/agents/` and `~/.codex/agents/` get **native TOML** generated from
the Markdown via `scripts/build_codex_agents.py`. User-level `~/.cursor/agents/` and
`~/.claude/agents/` also receive Markdown.

## Resume / partial runs

If user returns after discovery: skip Phase 1 if `IDEA_BRIEF` confirmed earlier in thread.
If experts done but math pending: start Phase 3 only.

## References

- [expert-evidence-package.md](references/expert-evidence-package.md) — per-agent JSON schemas
- [evidence-package.schema.json](references/evidence-package.schema.json) — machine-checkable JSON Schema for the merged input
- [scoring-formula.md](references/scoring-formula.md) — BRS formula & blocking rules
- [report-template.md](references/report-template.md) — final output format
- [evidence-status.md](references/evidence-status.md) — source grading
- [forbidden-phrases.md](references/forbidden-phrases.md) — banned language
- [example-input.json](references/example-input.json) / [example-output.json](references/example-output.json) — worked example
