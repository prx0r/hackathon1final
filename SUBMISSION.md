# Aletheia — Submission

## Submission details

| Field | Value |
|-------|-------|
| Title | Aletheia — Verified State Freshness for AI Agents |
| Theme | Hack Hydra: Build |
| Team | Solo |

## What we built

A verification boundary between OpenAIRE evidence access and persistent agent knowledge. When the OpenAIRE Graph changes, Aletheia identifies which agent conclusions need re-verification and emits proof obligations with frozen resolution criteria.

## Why it matters

AI agents are becoming the primary consumers of scholarly data. When they derive conclusions from OpenAIRE, those conclusions persist in memory, reports, dashboards, and other agents' contexts. When OpenAIRE changes, those conclusions may become stale. Nobody tells the agent.

Aletheia fills that gap.

## The demo (3 steps)

1. Agent queries OpenAIRE, stores conclusion with dependencies
2. OpenAIRE changes, Aletheia detects affected conclusions
3. Agent re-verifies affected conclusions, receipts signed

## Technical highlights

- HydraDB as storage layer (not decoration)
- Ed25519 signed verification receipts
- Frozen resolution plans
- Deterministic before/after fixtures
- 33/33 tests passing
- No in-memory fallback
- Four evidence kinds with explicit certification levels

## Sponsor integration

HydraDB is the storage backbone. All state lives in the graph. OpenCypher queries for dependency traversal. algo.MSpaths for path verification. Bolt compatibility for client access. Without HydraDB, Aletheia cannot function.

## Limitations

- Dependencies are manually declared, not auto-extracted
- Deterministic fixtures, not arbitrary real-world changes
- Single-agent scope (cross-agent trust is future work)
- No hosted deployment required for core demo
