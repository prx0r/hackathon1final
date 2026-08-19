# Final External Review

*Honest assessment: 8.5/10 idea, 8/10 engineering, 6.5/10 presentation → 9/10 potential with one reframe.*

---

## The core idea is strong

> "OpenAIRE tells an agent what research says now. Pāṭala tells it whether what the agent concluded before still follows."

That's genuinely more original than another literature-search UI.

## The presentation is weak

Current framing: "Continuous Verification for Agentic Science"
Problem: requires understanding CI, dependency tracking, provenance, derived state, semantic graph changes, proof obligations, resolution plans before caring.

Better: **"Freshness Receipts for AI Research"** or **"CI for Agent Memory"**

## The technical bug

The relation diff compares raw tuples: `(source, relation, target)`

The v11.3.0 migration remapped `IsCitedBy(A,B)` → `Cites(B,A)`. Without canonicalization, Aletheia would flag this as a change when it's actually the same scholarly proposition.

**Fix:** Normalize relations so `IsCitedBy(A,B) ≡ Cites(B,A)`.

## The demo should be 3 changes

1. Irrelevant metadata → CURRENT (shows precision)
2. Representational migration → CURRENT (shows semantic intelligence)
3. Actual evidence change → RECHECK (shows value)

## Submission hygiene issues

- Repo name: Alethiea (typo) vs Aletheia (correct)
- Links point to wrong repos
- Old strategic debris on front page
- Self-score too generous (25/30, not 27.5/30)

## The ranking

1. **Freshness Receipts** — best submission
2. Agent Memory CI — same thing, more futuristic
3. Current framing — technically excellent, harder to understand
4. Living Literature Review — clearer but less original
5. Research metric drift — useful but boring
