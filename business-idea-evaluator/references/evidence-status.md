# Evidence Status Labels

Every material claim in expert outputs must use one status:

| Status | Code | Meaning |
|--------|------|---------|
| Source-confirmed | `S1` | Single reliable source with URL |
| Multi-source | `S2` | 2+ independent sources agree |
| Indirect signal | `S3` | Proxy data (search volume, forums, analog behavior) |
| Hypothesis | `H0` | No source; logical inference only |
| Needs verification | `NV` | Critical gap; must test before decision |

## Source record format

```json
{
  "title": "Competitor X pricing page",
  "url": "https://...",
  "confirms": "market pays $29/mo for similar tool",
  "freshness": "2026-03",
  "reliability": 7,
  "market_match": "US SaaS — may not transfer to RU"
}
```

## When internet unavailable

Prefix report section:

> Интернет недоступен: сайты, конкуренты, свежая статистика не проверены. Рыночные выводы = гипотезы (H0/NV).

Downgrade all `S1`/`S2` to `H0`. Set `source_quality_index` cap at 3/10 in math layer.
