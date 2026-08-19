# The Numbers That Matter

*Why Aletheia is not a nice-to-have — it's infrastructure.*

---

## OpenAIRE changes every month

From 10 releases (v10.4.0 → v11.3.0):

| Metric | Per release | Per year |
|--------|-------------|----------|
| Products added | ~4.5M | ~54M |
| Relations changed | ~151M | ~1.8B |
| Affiliations changed | ~18M | ~216M |

**Every month, ~150M relations change.** Any agent conclusion depending on those relations may be stale within 30 days.

---

## The v11.3.0 bomb

August 4, 2026: OpenAIRE removed **318.7M redundant relations** in one release. This wasn't metadata noise — it was structural cleanup (IsCitedBy → Cites remapping). Every agent conclusion that depended on those relations is now potentially wrong.

---

## MCP adoption is exploding

- 10,000+ active public MCP servers
- 97 million monthly SDK downloads
- 200%+ YoY growth
- Alien: 29 tools for OpenAIRE connector, 600M+ products
- Claude Agent SDK powering research agents

---

## Agent usage projections

| Scenario | Agents | Queries/day | Queries/year |
|----------|--------|-------------|--------------|
| Conservative (2026) | 100 | 500 | 182,500 |
| Moderate (2027) | 1,000 | 10,000 | 3,650,000 |
| Aggressive (2028) | 10,000 | 200,000 | 73,000,000 |

---

## Cost per query (Claude via Alien)

~11,000 input + 500 output tokens per OpenAIRE search:

| Model | Cost/query |
|-------|-----------|
| Haiku | $0.003 |
| Sonnet | $0.04 |
| Opus | $0.20 |

---

## Annual cost projections (Sonnet)

| Scenario | Without Pāṭala | With Pāṭala (30%) | Saved |
|----------|---------------|-------------------|-------|
| 100 agents | $7,391 | $2,217 | $5,174 |
| 1,000 agents | $147,825 | $44,348 | $103,478 |
| 10,000 agents | $2,956,500 | $886,950 | $2,069,550 |

---

## The compounding problem

```
Month 1:  100 conclusions
Month 2:  150 conclusions (50 new + 100 old)
Month 3:  200 conclusions
...
Month 12: 1,200 conclusions

Without Pāṭala:
  1,200 conclusions, unknown which are stale
  Rerun all (expensive) or trust all (dangerous)

With Pāṭala:
  1,200 conclusions, 30 need re-verification
  Rerun 30, skip 1,170
  Cost: 2.5% of full rerun
```

---

## The real cost isn't compute

It's wrong conclusions acted upon:

- Policy team uses stale bibliometric analysis → wrong funding decision
- Research agent recommends wrong paper based on stale citation count
- Institutional dashboard shows outdated OA metrics → wrong compliance report
- AI assistant gives wrong answer because source data changed

**Cost of one wrong policy decision: >> $100,000**

**Pāṭala cost per check: ~$0.01**

---

## The proof

Aletheia's lineage benchmark:

```
3 source changes → 10 derived artifacts
Precision: 1.00 (0 false positives)
Recall: 1.00 (0 false negatives)
Recompute avoided: 50%
```

Deterministic. Reproducible. Proven.
