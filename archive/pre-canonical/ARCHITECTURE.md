# Architecture

## The continuity loop

```
Alien/OpenAIRE MCP
        ↓
source-preserving observation
        ↓
verified EvidenceBinding
        ↓
      LINEAGE DAG
 observation → claim → calculation → report → recommendation
        │
        │ upstream evidence changes
        ▼
   BLAST RADIUS
  /            \
unaffected    affected
  reuse           │
                  ▼
          PROOF OBLIGATION
                  │
          frozen ResolutionPlan
                  │
                  ▼
         VerificationReceipt
```

## Modules

| Module | Purpose |
|--------|---------|
| `openaire.py` | V3 adapter with source health |
| `compiler.py` | Trace → observations → dependencies |
| `lineage.py` | DAG with 9 artifact kinds, trust edges |
| `diff.py` | Semantic diff with materiality classification |
| `impact.py` | Blast radius computation |
| `obligations.py` | Proof obligation generation |
| `verification.py` | Resolution plans + receipts |
| `merkle.py` | RFC-6962 Merkle proofs |
| `attestation.py` | in-toto Statement v1 + Ed25519 |
| `provenance_guard.py` | Fail-closed evidence binding |
| `crux.py` | Structural crux ranking |
| `mcp_gateway.py` | Hardened MCP client |
| `mcp_trace.py` | Trace capture + redaction |
| `learning.py` | Wilson confidence + Thompson bandit |
| `ledger.py` | Hash-chained event store |

## Invariants

```
SOURCE FAILURE ≠ ZERO RESULTS
PARTIAL SOURCE ≠ COMPLETE RESULT SET
COSMETIC CHANGE ≠ MATERIAL CHANGE
UPSTREAM CHANGE ≠ CONCLUSION FALSE
AGENT SAYS "FIXED" ≠ PROVEN RESOLUTION
```
