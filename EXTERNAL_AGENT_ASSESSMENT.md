# External Agent Assessment — Final

*Honest audit of Alien repos + 2026 research vs our product claims.*

---

## What Alien actually has

| Evidence | Finding |
|----------|---------|
| Agents persist state? | **Partially.** Sessions persist, but conclusions are not structured durable claims. |
| Track what agents derive? | **During execution yes, long-term no.** JobProgress is ephemeral (deleted after 1 hour). |
| Stale-memory issues? | **None found in public repos.** No documented production incident. |
| MCP stores results? | **No.** Cache is in-memory with TTL. Output enters session transcripts only. |
| Tooling for stale knowledge? | **Yes — active research area in 2026.** Multiple projects. |
| How many agents? | **Unknown.** Dynamic subagent spawning, no public fleet count. |
| What do results become? | **Conversation/session state.** Not dependency-tracked knowledge. |

## What the 2026 research says

| Paper | Date | Key finding |
|-------|------|-------------|
| STALE | May 2026 | Best system: 55.2% accuracy at detecting stale memories |
| Temporal Validity in RAG | Jun 2026 | Conventional RAG has no temporal validity; structured supersession helps |
| When Memory Updates but Behavior Does Not | Aug 2026 | Corrected memory still contains implicit stale dependencies |

## Existing tools tackling this

| Tool | What it does |
|------|-------------|
| agent-memory-mcp | Provenance, freshness scores, stale/outdated states, drift_scan |
| agentmem | Stale memory detection via source hash changes |
| Graphiti | Temporal facts with supersession |
| agent-coherence | Detects stale cached views of shared mutable state |

## The defensible gap

Not "agents have stale memory" (too broad, already demonstrated).
Not "we add timestamps" (already crowded).

**Derived-state invalidation across external MCP dependencies.**

Alien runs stateful research agents against mutable OpenAIRE MCP, performs multi-agent derived synthesis, and produces tool-level provenance during execution — but does not durably preserve dependency relationships between external observations and derived claims.

## The honest claim

> Alien exposes all three ingredients needed for the failure mode — persistent agent sessions, externally sourced mutable research data, and multi-step derived research synthesis — but does not durably preserve dependency relationships between external observations and derived claims.

No documented production incident. But the failure mode is real and independently validated by 2026 research.
