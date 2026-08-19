# Aletheia — Submission

## Submission details

| Field | Value |
|-------|-------|
| Title | Aletheia — Verified State Freshness for AI Agents |
| Theme | OpenAIRE AI Hackathon: Build |
| Team | Solo |

## What we built

A verification boundary between OpenAIRE evidence access and persistent agent knowledge. When the OpenAIRE Graph changes, Aletheia identifies which agent conclusions need re-verification and emits proof obligations with frozen resolution criteria.

## Why it matters

AI agents are becoming the primary consumers of scholarly data. When they derive conclusions from OpenAIRE, those conclusions persist in memory, reports, dashboards, and other agents' contexts. When OpenAIRE changes, those conclusions may become stale. Nobody tells the agent.

Aletheia fills that gap.

## The demo (3 steps)

1. Agent queries OpenAIRE via Alien MCP, stores conclusion with dependencies
2. OpenAIRE changes, Aletheia detects affected conclusions
3. Agent re-verifies affected conclusions, receipts signed

## Technical highlights

- OpenAIRE V3 adapter with source-health semantics
- Content-addressed snapshots (JCS + SHA-256)
- Ed25519 signed verification receipts
- Frozen resolution plans
- Deterministic before/after fixtures
- 33/33 tests passing
- No in-memory fallback
- Four evidence kinds with explicit certification levels

## Sponsor integration

OpenAIRE provides the scholarly graph. Alien MCP provides agent access. Aletheia provides the continuity layer between them.

The official OpenAIRE MCP through Alien is the AI discovery plane. Aletheia records what evidence the agent used, tracks dependencies, and detects when those dependencies change.

Without OpenAIRE, there is no source data. Without Alien, there is no agent access. Without Aletheia, conclusions silently go stale.

## Limitations

- Dependencies are manually declared, not auto-extracted
- Deterministic fixtures, not arbitrary real-world changes
- Single-agent scope (cross-agent trust is future work)
- No hosted deployment required for core demo
