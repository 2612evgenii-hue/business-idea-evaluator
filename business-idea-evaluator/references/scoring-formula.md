# Business Reality Score (BRS) Formula

## Principle

**No arithmetic mean.** Multiplicative model with blocking caps. Final number comes from `scripts/calculate_brs.py`.

```
BRS = BasePotential × EvidenceFactor × SourceQuality × Execution × Money × Defense × Durability × RiskMultiplier × SensitivityMultiplier
```

Scale: 0–100 (script normalizes).

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
