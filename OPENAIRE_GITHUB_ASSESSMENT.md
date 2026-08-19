# What OpenAIRE's GitHub Actually Shows

*Honest assessment of OpenAIRE's repos vs our product.*

---

## What I found in openaire/iis (1,625 issues)

Backend infrastructure only:
- k8s migration
- Reference extraction (Crossref, COVID-19)
- Fuzzy citation matching
- SQLite database builders
- OpenAIRE ID generation
- Affiliation enrichment

**Nothing related to MCP, agents, or derived conclusions.**

## Why

OpenAIRE's repos are about **Graph production**. The MCP/consumer side is handled through Alien. Nobody is building the "what happens to conclusions" layer.

```
OpenAIRE: builds the source
Alien: makes it accessible
Nobody: tracks what agents derive from it

Aletheia: fills the gap
```

## The honest assessment

**For the hackathon:** Yes, novel, technically sound, demonstrates a real gap.

**For production:** Maybe — only if agents persist conclusions, OpenAIRE changes break them, and someone tracks dependencies.

**The honest pitch:**
> "Nobody is tracking what agents derive from OpenAIRE. We built the first tool to do that. It works. The problem is real but narrow. It becomes critical as agents scale."

**NOT:** "Everyone needs this immediately" or "It saves millions of dollars."
