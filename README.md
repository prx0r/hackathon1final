# Aletheia

**Verified state freshness for AI agents on OpenAIRE.**

> **No proof obligation → no trusted conclusion.**

An agent deriving a conclusion from OpenAIRE evidence is an **observation**, not proof that the conclusion remains valid. Aletheia puts one small verification boundary between evidence access and persistent agent knowledge:

```text
Agent queries OpenAIRE via Alien MCP
              ↓
        evidence captured
              ↓
        dependencies recorded
              ↓
    conclusion stored with lineage
              ↓
         OpenAIRE changes
              ↓
      blast radius computed
              ↓
    affected conclusions flagged
              ↓
       proof obligation emitted
              ↓
  frozen resolution plan
              ↓
     verification receipt
              ↓
    conclusion returns to CURRENT
```

**The agent cannot declare its own conclusions current.** Downstream actions consume only conclusions backed by a PASS verification receipt, never stale cached state.

---

## The problem

Alien Intelligence has made OpenAIRE agent-accessible via MCP. Agents can now query 600M+ research products, explore citations, analyze author networks, and synthesize findings.

That creates a new problem:

> **What happens to those conclusions when OpenAIRE changes?**

OpenAIRE's August 2026 release added 6.43M products and removed 318.7M redundant relations. Any agent conclusion depending on those relations is now potentially wrong. Nobody told the agent.

Aletheia solves only that boundary.

It does **not** replace OpenAIRE, Alien MCP, HydraDB, or any agent framework. It makes agent conclusions auditable against their evidence over time.

---

## Two-minute demo

### 1. Agent queries, concludes, stores

Agent uses Alien MCP to query OpenAIRE for AI research software.

```text
OpenAIRE returns: 175 products
Agent concludes: "Found 175 AI research software products"
Agent stores conclusion with dependencies on 10 tracked entities
```

### 2. OpenAIRE changes, Aletheia detects

OpenAIRE updates. 2 of the 10 tracked entities are gone.

```text
Aletheia checks: 8 entities still present, 2 gone
Affected conclusions: 2
Unaffected conclusions: 4

Proof obligation emitted:
  "Re-verify: entity X disappeared from current OpenAIRE state"
```

### 3. Agent re-verifies, conclusion restored

Agent rechecks the 2 affected conclusions against current OpenAIRE.

```text
Conclusion C1: re-verified → VERIFIED_CURRENT
Conclusion C2: re-verified → VERIFIED_CURRENT

Verification receipt signed and stored.
All 6 conclusions now carry valid receipts.
```

---

## Why HydraDB is essential

Aletheia stores all state in HydraDB OSS:

- Graph lineage (dependencies, receipts, claims)
- Snapshot digests
- Verification receipts with Ed25519 signatures
- Append-only event history

HydraDB provides: snapshot-consistent OpenCypher, durable graph state, GraphBLAS-backed traversal, Bolt compatibility, native bounded path procedures.

**The graph-level invariant:** every trusted conclusion has a path:

```
Conclusion
  └─ VERIFIED_BY → PASS Receipt
                      └─ VERIFIES → Snapshot
                                      ├─ DEPENDS_ON → Evidence
                                      └─ FROM → Query
```

---

## Anti-cheat design

Four kinds of evidence:

| Evidence | What it proves | Counts as live proof? |
|----------|---------------|----------------------|
| Unit tests | local policy/signature logic | No |
| Deterministic fixtures | reproducible before/after | Partly |
| HydraDB graph operations | real graph execution | Partly |
| Full certification gate | HydraDB container + algo.MSpaths | **Yes** |

There is intentionally:
- No in-memory fallback
- No skip-if-Hydra-absent in certification
- No pass certificate if HydraDB was not run
- No claim that Ed25519 signature proves semantic correctness (it proves receipt integrity)

---

## Quick start

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'

# Deterministic demo
python3 -m aletheia.cli demo

# Live certification (requires Docker)
./scripts/certify.sh
```

---

## What this unlocks

Once "successful conclusion" means **verified conclusion**, the graph can support:

- routing by **cost per verified conclusion** rather than cost per call
- self-healing workflows that retry verified failures
- multi-step plans where next step requires verified predecessor
- capability reputation computed from certified outcomes
- audit questions: "why was this conclusion trusted?" via graph traversal

---

## Repository map

```
src/aletheia/         core: models, engine, verifiers, receipts, Hydra client
fixtures/             deterministic before/after snapshots
tests/                policy, signature, integration
scripts/              certification, smoke tests
docs/                 architecture, evidence model, limitations
```
