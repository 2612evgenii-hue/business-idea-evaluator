# Business Reality Score (BRS) Formula

## Principle

**No arithmetic mean.** The final number comes from `scripts/calculate_brs.py`.

The model uses a **weighted geometric mean** of all 9 factors, scaled to 0–100, then applies blocking caps:

```
BRS = 100 × weighted_geomean(BasePotential, EvidenceFactor, SourceQuality, Execution,
                             Money, Defense, Durability, RiskMultiplier, SensitivityMultiplier)
```

Why a weighted geometric mean and not a raw product or arithmetic mean:
- A raw product of nine sub-1.0 factors underflows toward 0 (a viable idea would score ~1/100).
- An arithmetic mean hides blocking weaknesses (a fatal factor gets averaged away).
- The geometric mean keeps the result in a usable 0–100 range, yet a single very low
  factor still drags the score down hard. Hard blocks are enforced separately via caps below.

Factor weights (more pull where failure is most decisive):

| Factor | Weight |
|--------|--------|
| Money | 1.4 |
| RiskMultiplier | 1.4 |
| BasePotential | 1.3 |
| EvidenceFactor | 1.1 |
| SensitivityMultiplier | 1.1 |
| Execution | 1.0 |
| SourceQuality | 0.9 |
| Defense | 0.9 |
| Durability | 0.9 |

All factors are normalized to [0,1] internally. RiskMultiplier and SensitivityMultiplier are
penalties in [0.1, 1.0]; the rest are potentials in [0,1]. **Money** is additionally gated by a
unit-economics modifier from agent 16 (LTV/CAC ratio, gross margin, payback). **SourceQuality**
is capped at 0.3 when no sources exist or `internet_available=false`.

## Factor definitions (0–1 internally)

| Factor | Primary inputs (expert scores 0–10) |
|--------|-------------------------------------|
| BasePotential | 02 pain_strength, pain_frequency, willingness_to_pay; 03 audience_access; 04 market_timing, local_fit |
| EvidenceFactor | 13 evidence_index / 10 |
| SourceQuality | 13 source_quality_index / 10 |
| Execution | 08 technical_feasibility, dev_speed; inverse external_dependency |
| Money | 06 money_potential, revenue_repeatability; 16 financial_feasibility |
| Defense | 10 defensibility, retention_potential; inverse copyability |
| Durability | 05 long_term_potential; inverse obsolescence_risk, hype_dependency |
| RiskMultiplier | 1 − (max of 09 legal/platform risks, 12 failure_risk) / 10, floor 0.1 |
| SensitivityMultiplier | 1 − (17 fragility_index / 10) × 0.5 |

## Blocking caps (applied after product)

| Condition | Cap on final BRS |
|-----------|------------------|
| legal_safety < 3 | max 35 |
| willingness_to_pay < 4 | max 45 |
| evidence_index < 3 | max 40, label "hypothesis only" |
| source_quality_index < 3 | max 45 |
| technical_feasibility < 3 | max 40 |
| blocking_legal_risk = 1 | max 25 |
| LTV < CAC in realistic scenario | max 30 |
| failure_risk ≥ 8 | max 35 |

## Input file for script (`biz-eval-input.json`)

```json
{
  "idea_brief": "...",
  "experts": { "01": { "scores": {}, "math_params": {} }, ... },
  "math": {
    "13": {},
    "14": {},
    "15": {},
    "16": {},
    "17": {},
    "18": {}
  }
}
```

## Output interpretation

| BRS | Verdict |
|-----|---------|
| 65–100 | Test in narrow segment with experiments |
| 45–64 | Reformulate before investment |
| 25–44 | Weak — cheap tests only |
| 0–24 | Do not launch current form |

Always report: min / base / max range, confidence, top uncertainty, top blocker.
