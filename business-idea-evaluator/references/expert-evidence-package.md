# Expert Evidence Package — JSON Schema

Each expert agent returns **only** this JSON structure (no prose outside JSON).
The machine-checkable JSON Schema for the merged package is
[`evidence-package.schema.json`](evidence-package.schema.json); validate with
`scripts/validate_evidence_package.py`.

**Mandatory for all 12 experts:** `summary`, `findings`, `sources`, `scores`,
`evidence_level`, `confidence`, `hypotheses`, `risks`, `math_params`.

## Common expert output schema

```json
{
  "agent_id": "01",
  "agent_name": "analog-research",
  "idea_brief_hash": "<optional short id>",
  "summary": "2-4 sentences, factual",
  "findings": ["bullet facts with evidence codes S1/S2/S3/H0/NV"],
  "sources": [
    {"title": "", "url": "", "confirms": "", "freshness": "", "reliability": 0, "market_match": ""}
  ],
  "hypotheses": ["unproven assumptions"],
  "risks": ["specific risks"],
  "scores": {
    "primary_metric": 0,
    "secondary_metric": 0,
    "tertiary_metric": 0
  },
  "evidence_level": 0,
  "confidence": 0,
  "math_params": {
    "param_name": 0.0
  }
}
```

## Per-agent score keys (scores object)

| ID | Agent | scores keys (0–10 each) |
|----|-------|-------------------------|
| 01 | analog-research | `novelty`, `competition_saturation`, `search_confidence` |
| 02 | pain-demand | `pain_strength`, `pain_frequency`, `willingness_to_pay`, `demand_proof` |
| 03 | audience-behavior | `audience_access`, `sales_difficulty`, `decision_speed` |
| 04 | market-country | `market_timing`, `country_risk`, `local_fit` |
| 05 | trends-longevity | `long_term_potential`, `hype_dependency`, `obsolescence_risk` |
| 06 | monetization | `money_potential`, `revenue_repeatability`, `monetization_scale` |
| 07 | marketing | `marketing_difficulty`, `organic_growth`, `product_trust` |
| 08 | implementation | `technical_feasibility`, `dev_speed`, `external_dependency` |
| 09 | legal-platform | `legal_safety`, `platform_stability`, `ethical_cleanliness` |
| 09 | (risks) | also pass `math_params.max_legal_risk` 0–10 |
| 10 | competitive-moat | `defensibility`, `copyability`, `retention_potential` |
| 11 | launch-zero | `startup_practicality`, `validation_speed`, `first_sales_difficulty` |
| 12 | red-team | `failure_risk`, `assumption_fragility`, `kill_shot_severity` |

## math_params (experts → math layer)

Experts must populate `math_params` where applicable:

- `01`: `direct_analogs_count`, `substitutes_count`
- `02`: `estimated_wtp_usd_monthly` (range midpoint)
- `06`: `estimated_arpu_monthly`, `estimated_gross_margin_pct`
- `08`: `mvp_weeks`, `needs_code_bool` (0/1)
- `09`: `blocking_legal_risk` (0/1)
- `12`: `top_kill_factor_weight` 0–10

## Merged package (orchestrator builds)

```json
{
  "idea_brief": "...",
  "confirmed_at": "ISO date",
  "internet_available": true,
  "experts": { "01": {}, "02": {}, ... "12": {} },
  "failed_agents": []
}
```

## Math agent output schemas (13–18)

### 13 evidence-stats

```json
{
  "agent_id": "13",
  "evidence_index": 0,
  "source_quality_index": 0,
  "source_freshness_index": 0,
  "local_applicability_index": 0,
  "statistical_confidence_index": 0,
  "proven_theses": [],
  "unproven_theses": [],
  "source_backed_theses": [],
  "needs_verification": []
}
```

### 14 math-model

```json
{
  "agent_id": "14",
  "formula_description": "string",
  "variables": [{"name": "", "weight": 0.0, "value": 0.0, "blocking": false}],
  "blocking_rules_triggered": [],
  "preliminary_brs_range": {"min": 0, "base": 0, "max": 0}
}
```

### 15 scenario-probability

```json
{
  "agent_id": "15",
  "scenarios": {
    "pessimistic": {"description": "", "probability_pct": 0},
    "base": {"description": "", "probability_pct": 0},
    "optimistic": {"description": "", "probability_pct": 0},
    "stress": {"description": "", "probability_pct": 0}
  },
  "outcome_map": {
    "total_failure_pct": 0,
    "small_service_income_pct": 0,
    "sustainable_business_pct": 0,
    "scalable_business_pct": 0,
    "external_death_pct": 0
  }
}
```

### 16 unit-economics

```json
{
  "agent_id": "16",
  "scenarios": {
    "bad": {"cac": 0, "ltv": 0, "arpu": 0, "churn_monthly_pct": 0, "gross_margin_pct": 0, "payback_months": 0},
    "realistic": {},
    "good": {}
  },
  "customers_for_revenue": {"100k_rub_month": 0, "500k_rub_month": 0, "1m_rub_month": 0},
  "financial_feasibility": 0,
  "recurring_income_potential": 0,
  "economy_killers": []
}
```

### 17 sensitivity

```json
{
  "agent_id": "17",
  "top_parameters": [
    {"param": "", "baseline": 0, "if_worsens": "", "brs_impact": "high|medium|low"}
  ],
  "fragility_index": 0,
  "critical_assumptions": [],
  "zero_out_risks": []
}
```

### 18 experiments

```json
{
  "agent_id": "18",
  "priority_hypothesis": "",
  "experiments_7d": [],
  "experiments_30d": [],
  "experiments_90d": [],
  "success_metrics": {},
  "failure_metrics": {},
  "continue_criteria": [],
  "kill_criteria": []
}
```
