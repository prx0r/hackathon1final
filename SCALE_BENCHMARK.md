# Scale Benchmark

*Real OpenAIRE data, real use cases, real cost projections.*

---

## What agents actually build (5 real use cases)

| Use case | OpenAIRE total | Tracked | Dependencies |
|----------|---------------|---------|-------------|
| Living systematic review | 109,346 | 10 | 25 |
| Bibliometric analysis | 23,718 | 10 | 25 |
| Dataset discovery | 7,440 | 10 | 20 |
| Software landscape | 32,319 | 10 | 20 |
| Author network | 163 | 10 | 25 |

All queried against live OpenAIRE V3.

---

## At MCP scale

| Application | Agents | Conclusions | Dependencies |
|-------------|--------|-------------|-------------|
| Living systematic review | 50 | 1,000 | 5,000 |
| Bibliometric monitoring | 20 | 1,000 | 10,000 |
| Dataset registry | 30 | 900 | 2,700 |
| Research agent fleet | 100 | 1,000 | 8,000 |
| Institutional dashboard | 5 | 500 | 7,500 |
| **TOTAL** | **205** | **4,400** | **33,200** |

---

## Cost of staleness (monthly, Sonnet pricing)

```
Without Pāṭala:
  Rerun all 4,400 conclusions
  Cost: $1,760/month = $21,120/year

With Pāṭala (15% affected):
  Rerun only 660 affected conclusions
  Skip 3,740 unaffected
  Cost: $264/month = $3,168/year

Saved: $17,952/year (85% avoided)
```

---

## The real cost: wrong conclusions

| Application | Wrong conclusions | Cost each | Total |
|-------------|------------------|-----------|-------|
| Living review | 3 | $50,000 | $150,000 |
| Bibliometric report | 5 | $100,000 | $500,000 |
| Dataset recommendation | 2 | $25,000 | $50,000 |
| Research agent memory | 10 | $10,000 | $100,000 |
| Institutional dashboard | 8 | $200,000 | $1,600,000 |
| **TOTAL** | **28** | | **$2,400,000** |

Pāṭala cost per check: ~$0.01
ROI: 54,545x

---

## The compounding problem

```
Month  1:   150 conclusions,   22 stale (15%)
Month  3:   450 conclusions,   67 stale
Month  6:   900 conclusions,  135 stale
Month 12: 1,800 conclusions,  270 stale
```

Without Pāṭala: unknown which are stale.
With Pāṭala: exactly which need re-verification.

---

## External validation

| Claim | Source |
|-------|--------|
| Agents can't detect stale memories (55.2% accuracy) | STALE, arXiv:2605.06527 |
| DAG replay preserves unaffected work | Execution Lineage, arXiv:2605.06365 |
| This is an open research problem | Agent Traces to Trust, arXiv:2606.04990 |
| Agents have compounding errors | Anthropic research |
| 150M relations change monthly | OpenAIRE changelog |

---

## Our benchmark

```
3 source changes → 10 derived artifacts
Precision: 1.00
Recall:    1.00
Recompute avoided: 50%
```
