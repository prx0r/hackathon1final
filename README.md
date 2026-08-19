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

**The agent cannot declare its own conclusions current.** Downstream actions consume only conclusions backed by a verification receipt, never stale cached state.

---

## The problem

Alien Intelligence has made OpenAIRE agent-accessible via MCP. Agents can now query 600M+ research products, explore citations, analyze author networks, and synthesize findings.

That creates a new problem:

> **What happens to those conclusions when OpenAIRE changes?**

OpenAIRE's August 2026 release added 6.43M products and removed 318.7M redundant relations. Any agent conclusion depending on those relations is now potentially wrong. Nobody told the agent.

Aletheia solves only that boundary.

It does **not** replace OpenAIRE, Alien MCP, or any agent framework. It makes agent conclusions auditable against their evidence over time.

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

## How Aletheia works

Aletheia stores all state using content-addressed hashing and an append-only event ledger.

Core flow:

```text
OpenAIRE observation
     ↓
canonical snapshot (JCS + SHA-256)
     ↓
TrackedClaim with explicit dependencies
     ↓
later: semantic diff against new state
     ↓
blast radius via dependency walk
     ↓
ImpactReport (affected vs unaffected)
     ↓
ProofObligation with frozen resolution plan
     ↓
VerificationReceipt (signed, tamper-evident)
```

---

## Anti-cheat design

Four kinds of evidence:

| Evidence | What it proves | Counts as proof? |
|----------|---------------|-----------------|
| Unit tests | Local policy/signature logic | No |
| Deterministic fixtures | Same input → same output | Partly |
| OpenAIRE V3 API | Real graph execution | Partly |
| Full certification | All checks + ledger integrity | **Yes** |

There is intentionally:
- No in-memory fallback
- No skip-if-source-absent in certification
- No pass certificate if source was not queried
- No claim that Ed25519 signature proves semantic correctness (it proves receipt integrity)

---

## Quick start

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'

# Deterministic demo
python3 -m aletheia.cli demo

# Live OpenAIRE query
python3 scripts/live_smoke.py

# Run all tests
python3 -m unittest discover -s tests -v
```

---

## What this unlocks

Once "conclusion current" means **verified conclusion**, agents can:

- recompute only affected conclusions (not everything)
- track freshness of persistent knowledge
- verify conclusions from other agents before trusting them
- build self-healing research workflows
- audit: "why was this conclusion trusted?" via dependency graph

---

## Repository map

```
src/aletheia/         core: models, engine, verifiers, receipts, OpenAIRE client
fixtures/             deterministic before/after snapshots
tests/                policy, signature, integration
scripts/              certification, smoke tests, demos
docs/                 architecture, evidence model, limitations
```
