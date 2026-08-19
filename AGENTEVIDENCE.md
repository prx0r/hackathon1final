# Agent Evidence — What We Now Know

*After reviewing OpenAIRE posts, strategy pages, Alien's technical essays, the live plugin, and actual agent code.*

---

## The timeline of evidence

| Date | What they said | What exists | Status |
|------|---------------|-------------|--------|
| Apr 2026 | OpenAIRE announces first MCP for scholarly intelligence | Alien has real OpenAIRE use-case page | Built |
| May 2026 | OpenAIRE describes autonomous agents reasoning across sources | Plugin and workflows exist | Implemented |
| Jun 2026 | Alien publishes agent architecture + internal research agents | Production harness running over OpenAIRE bibliometric MCP | Running |
| Jun 2026 | OpenAIRE strategy: AI-enabled research workflows as priority | Person entities, ORCID, affiliations already in Graph | Strategic |
| Aug 2026 | Graph v11.3.0: +6.43M products, -318.7M relations | Mutable upstream source | Real |

---

## What Alien has actually built

**Alien explicitly says its internal research agents use an OpenAIRE bibliometric MCP.** (Alien Club, "What a Harness Actually Has to Do")

Their OpenAIRE frontend:
- `persistSession: true` — sessions survive restarts
- `resumeSessionId` — can resume prior research
- Subagent delegation — root agent spawns specialists
- `JobProgress` stores tool calls, research data, session ID

Their AI SRE stores incident memory in SQLite, checks past incidents before investigating new ones, and uses verdicts to alter future behavior. (Alien Club, "We're a 3-Person Tech Team")

**Three components independently demonstrated by Alien:**
1. Agents derive judgments from OpenAIRE ✓
2. Judgments/state persist ✓
3. External sources evolve ✓

**What Alien does NOT have:** durable dependency tracking between observations and derived claims.

---

## What OpenAIRE explicitly expects

OpenAIRE says agents should:
- Reason across sources
- Plan tasks
- Follow relationships
- Perform literature reviews, citation analysis, author mapping, dataset discovery

They frame this as "systems that increasingly interpret scientific knowledge" grounded in public, governed infrastructure. (OpenAIRE, May 2026)

**OpenAIRE itself says agents should derive research intelligence. We don't have to imagine it.**

---

## The gap Alien leaves open

Alien already solves:
- Current source data (automatic updates)
- Current MCP semantics (automated auditor loop)
- Execution tracing (JobProgress)
- Session persistence (PostgreSQL)

Alien does NOT solve:
- Durable dependency tracking between observations and derived claims
- Invalidation propagation when upstream changes
- Selective revalidation of affected conclusions
- Freshness receipts for persistent agent knowledge

```
Alien:
source → tool → execution → session

Aletheia:
execution → claim → dependency → future change → revalidation
```

---

## The evidence chain

```
OPENAIRE SAYS:
agents should interpret its Graph and perform
multi-step research analysis
                     ↓
ALIEN SAYS:
its internal research agents already use
an OpenAIRE bibliometric MCP
                     ↓
ALIEN CODE SHOWS:
OpenAIRE agents can delegate to subagents
and persist/resume sessions
                     ↓
OPENAIRE SHOWS:
the underlying Graph continually changes
                     ↓
ALIEN ALREADY SOLVES:
current source data
current MCP semantics
execution tracing
session persistence
                     ↓
BUT NO PUBLIC LAYER CONNECTS:
an old derived conclusion
         ↓
the exact observations it depended upon
         ↓
later semantic source changes
         ↓
targeted revalidation
```

**That is the case.**

---

## Sources

| Claim | Source |
|-------|--------|
| OpenAIRE expects multi-step research intelligence | OpenAIRE, "OpenAIRE and Alien Intelligence", May 2026 |
| Alien built OpenAIRE MCP | OpenAIRE Innovation, Apr 2026 |
| Alien runs internal research agents | Alien Club, "What a Harness Actually Has to Do" |
| Alien agents persist sessions | Alien Club, "We Didn't Build an Agent Framework" |
| Alien SRE stores incident memory | Alien Club, "We're a 3-Person Tech Team" |
| Graph changes are real | OpenAIRE changelog, v11.3.0 |
| Independent users observe drift | Hackathon repos (small-N) |
| No documented stale-conclusion incident | Checked Alien/OpenAIRE repos |
| No public dependency-tracking layer | Checked all repos |
