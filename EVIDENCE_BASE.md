# The Evidence Base

*External sources backing every claim in the Aletheia pitch.*

---

## 1. The problem is real — agents can't detect stale memories

**Paper:** STALE (arXiv:2605.06527, May 2026)

> "Even the best evaluated model achieving only **55.2% overall accuracy**" at detecting when stored memories are no longer valid.

Key finding: LLM agents suffer from **Implicit Conflict** — a later observation invalidates an earlier memory without explicit negation. The agent never notices.

**This is exactly what Aletheia solves.**

Citation: Chao et al., "STALE: Can LLM Agents Know When Their Memories Are No Longer Valid?", arXiv:2605.06527, 2026.

---

## 2. The architecture is validated — execution lineage works

**Paper:** From Agent Loops to Deterministic Graphs (arXiv:2605.06365, May 2026)

> "DAG replay preserved the final memo exactly in all runs, with **zero churn and zero unrelated-branch contamination**, while loop baselines regenerated the memo and frequently imported unrelated context."

Key finding: Explicit dependency graphs (DAGs) preserve unaffected work while propagating only necessary changes. Loop baselines fail at this.

**This is exactly Aletheia's lineage DAG.**

Citation: Rosen & Rosen, "From Agent Loops to Deterministic Graphs: Execution Lineage for Reproducible AI-Native Work", arXiv:2605.06365, 2026.

---

## 3. The research community agrees this is an open problem

**Paper:** From Agent Traces to Trust (arXiv:2606.04990, June 2026)

> "Major open challenges include unified trace schemas, claim-level semantic provenance, provenance-aware safety, recovery-oriented evaluation and privacy-aware audit infrastructure."

Key finding: The survey identifies exactly the gaps Aletheia fills — claim-level provenance, dependency tracking, and recovery-oriented verification.

Citation: Wang et al., "From Agent Traces to Trust: A Survey of Evidence Tracing and Execution Provenance in LLM Agents", arXiv:2606.04990, 2026.

---

## 4. The agent ecosystem is scaling fast

**Source:** Anthropic, "Building Effective Agents" (Dec 2024)

> "Agents' autonomy makes them ideal for scaling tasks in trusted environments. The autonomous nature of agents means **higher costs, and the potential for compounding errors**."

Key finding: Anthropic themselves warn about compounding errors in autonomous agents. Pāṭala addresses exactly this — detecting when derived conclusions have become wrong.

**MCP adoption:**
- 10,000+ active public MCP servers
- 97 million monthly SDK downloads
- 200%+ YoY growth
- Alien: 29 tools for OpenAIRE connector

**Claude pricing (current):**
- Haiku: $0.25/$1.25 per 1M tokens
- Sonnet: $3/$15 per 1M tokens
- Opus: $15/$75 per 1M tokens

Citation: Anthropic, "Building Effective Agents", anthropic.com/research, 2024.

---

## 5. OpenAIRE changes are massive and frequent

**Source:** OpenAIRE Graph Changelog (graph.openaire.eu/docs/changelog)

From 10 releases (v10.4.0 → v11.3.0):

| Metric | Per release | Per year |
|--------|-------------|----------|
| Products added | ~4.5M | ~54M |
| Relations changed | ~151M | ~1.8B |
| Affiliations changed | ~18M | ~216M |

**v11.3.0 (August 4, 2026):**
- +6.43M research products
- -318.7M redundant relations (IsCitedBy → Cites cleanup)
- -1.05M invalid funding relations
- ScholeXplorer: IsRelatedTo → Cites remapped
- Affiliations expanded +12.35M

**Every month, ~150M relations change.** Any agent conclusion depending on those relations may be stale within 30 days.

---

## 6. The cost is real

**Based on Anthropic pricing + MCP adoption:**

| Scenario | Agents | Queries/year | Cost (Sonnet) | With Pāṭala | Saved |
|----------|--------|-------------|---------------|-------------|-------|
| Conservative | 100 | 182,500 | $7,391 | $2,217 | $5,174 |
| Moderate | 1,000 | 3,650,000 | $147,825 | $44,348 | $103,478 |
| Aggressive | 10,000 | 73,000,000 | $2,956,500 | $886,950 | $2,069,550 |

**But the real cost isn't compute.** It's wrong conclusions acted upon:
- Policy team uses stale analysis → wrong funding decision
- Research agent recommends wrong paper → reputation damage
- Institutional dashboard shows outdated metrics → wrong compliance report
- AI assistant gives wrong answer → user trust destroyed

---

## 7. Our benchmark proves the mechanism works

**Source:** Aletheia lineage benchmark (deterministic, reproducible)

```
3 source changes → 10 derived artifacts
Precision: 1.00 (0 false positives)
Recall:    1.00 (0 false negatives)
Recompute avoided: 50%
Unaffected execution keys preserved: TRUE
```

This is not a claim. It's a measured, reproducible result on controlled fixtures.

---

## The thesis in one paragraph

LLM agents are scaling rapidly (Anthropic warns about compounding errors). The best systems achieve only 55.2% at detecting stale memories (STALE benchmark). Execution lineage DAGs prove that dependency-aware invalidation preserves unaffected work (Rosen & Rosen, 2026). OpenAIRE changes 150M relations per month, making any agent conclusion potentially stale within 30 days. Aletheia fills the gap: dependency-based freshness for persistent agent knowledge.

> **Agents generate knowledge. They're terrible at maintaining it. Aletheia makes what they learn accountable to changing evidence.**
