# Aletheia — Architecture

## The continuity loop

```
OpenAIRE (source)
     ↓
Alien MCP (access)
     ↓
Agent (derives conclusion)
     ↓
Aletheia (records dependencies)
     ↓
OpenAIRE changes
     ↓
Aletheia (computes blast radius)
     ↓
Affected: PROOF OBLIGATION
Unaffected: NO ACTION
     ↓
Agent re-verifies
     ↓
Verification receipt (signed)
     ↓
Conclusion returns to CURRENT
```

## Core modules

| Module | Purpose |
|--------|---------|
| `openaire.py` | V3 adapter with source health |
| `compiler.py` | Trace → observations → dependencies |
| `lineage.py` | DAG with 9 artifact kinds, trust edges |
| `diff.py` | Semantic diff with materiality |
| `impact.py` | Blast radius computation |
| `obligations.py` | Proof obligation generation |
| `verification.py` | Resolution plans + receipts |
| `merkle.py` | RFC-6962 Merkle proofs |
| `attestation.py` | in-toto Statement v1 + Ed25519 |
| `mcp_gateway.py` | Hardened MCP client |
| `learning.py` | Wilson confidence + Thompson bandit |
| `ledger.py` | Hash-chained event store |

## Graph invariant

Every trusted conclusion has:

```
Conclusion
  └─ VERIFIED_BY → PASS Receipt
                      └─ VERIFIES → Snapshot
                                      ├─ DEPENDS_ON → Evidence
                                      └─ FROM → Query
```

## Invariants

```
SOURCE FAILURE ≠ ZERO RESULTS
PARTIAL SOURCE ≠ COMPLETE RESULT SET
COSMETIC CHANGE ≠ MATERIAL CHANGE
UPSTREAM CHANGE ≠ CONCLUSION FALSE
AGENT SAYS "FIXED" ≠ PROVEN RESOLUTION
```
