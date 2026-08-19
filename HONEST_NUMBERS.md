# Honest Numbers

*What we know vs what we assume.*

---

## What we actually know (measurable)

**OpenAIRE Graph:**
- 386.6M research products
- 237.2M publications, 106.5M datasets, 949.1K software
- 324 funders, 3.9M projects, 157K data sources
- Monthly releases
- Average 4.5M products added per release
- Average 151M relations changed per release

**MONITOR:** 122 dashboards (25 institutions, 13 funders, 76 initiatives, 8 publishers)

**MCP:** 10,000+ servers, 97M monthly downloads

**Claude pricing:** Sonnet $3/$15 per 1M tokens

**Our benchmark:** 100% precision, 100% recall on controlled fixtures, 50% recomputation avoided

---

## What we assume (projections)

| Question | We don't know | Assumption |
|----------|--------------|------------|
| How many agents use OpenAIRE? | Unknown | 100-1000 |
| How many conclusions persist? | Unknown | 50-200 per agent |
| What % are affected per update? | Unknown | 15% |
| Cost of rerunning? | Know Claude pricing, not actual usage | ~$0.40 per analysis |
| Cost of wrong conclusions? | Unknown | $50K-$500K |

---

## Honest savings (conditional)

**IF 100 agents × 50 conclusions each:**
- Conclusions: 5,000
- Affected: 750 (15%)
- Saved: $20,400/year
- ONLY IF: 100 agents exist, each stores 50 conclusions

**IF 1000 agents × 50 conclusions each:**
- Conclusions: 50,000
- Affected: 7,500 (15%)
- Saved: $204,000/year
- ONLY IF: 1000 agents exist, each stores 50 conclusions

---

## What we can't measure

- How many agents actually persist conclusions?
- How long do conclusions stay in memory?
- When OpenAIRE changes, do agents act on stale conclusions?
- What is the actual cost of a wrong agent answer?

Our benchmark proves the **mechanism** works. We don't have data proving the **problem** is widespread.

---

## The conservative pitch

> IF 100 research agents persist conclusions from OpenAIRE,
> AND 15% of those conclusions are affected by monthly Graph updates,
> THEN Aletheia saves ~$5,000/year in rerun costs.
>
> But the real value isn't compute savings.
> It's knowing WHICH conclusions to recheck.
>
> A wrong conclusion in a policy report costs >> $100,000.
> A wrong answer from a research agent costs trust.
> Aletheia doesn't prevent wrong conclusions.
> It tells you WHICH conclusions need rechecking.
