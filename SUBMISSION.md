# Aletheia — Submission

## Submission details

| Field | Value |
|-------|-------|
| Title | Aletheia — Freshness Receipts for AI Research |
| Theme | OpenAIRE AI Hackathon: Build |
| Team | Solo |

## What we built

Aletheia gives every OpenAIRE-derived agent conclusion a freshness receipt, then tells the agent exactly which conclusions need rechecking when the Graph changes.

## Why it matters

OpenAIRE and Alien Intelligence have built autonomous research agents that query 600M+ scholarly products, perform literature reviews, citation analyses, and cross-domain discovery. Alien already runs internal research agents over an OpenAIRE bibliometric MCP. Their sessions persist. Their conclusions survive across turns.

But when OpenAIRE changes — and it changes monthly, with 151M relations modified per release — those persisted conclusions may become stale. Nobody tells the agent.

Aletheia fills that gap: dependency-aware freshness tracking for persistent agent knowledge.

## The demo (3 steps)

1. Agent queries OpenAIRE via Alien MCP, stores conclusion with dependencies
2. OpenAIRE changes, Aletheia detects which dependencies are affected
3. Agent re-verifies affected conclusions, freshness receipt updated

## Technical highlights

- OpenAIRE V3 adapter with source-health semantics
- Content-addressed snapshots (JCS + SHA-256)
- Ed25519 signed verification receipts
- Frozen resolution plans
- Deterministic before/after fixtures
- 33/33 tests passing
- No in-memory fallback

## Sponsor integration

Alien makes research intelligence accessible. Aletheia makes what agents learn maintainable. The official OpenAIRE MCP through Alien is the discovery plane. Aletheia tracks what evidence was used and detects when that evidence changes.

Alien already solves: current source data, current MCP semantics, execution tracing, session persistence.

Aletheia solves: **maintaining the validity of what agents derived after the underlying research intelligence changes.**

## Limitations

- Dependencies manually declared, not auto-extracted from prose
- Deterministic fixtures, not arbitrary real-world changes
- Single-agent scope (cross-agent trust is future work)
- No hosted deployment required for core demo
