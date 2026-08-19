# Alien Intelligence — Full Documentation Summary

*Compiled from alien.club, docs.alien.club, hackathon page*

---

## What Alien Is

A data platform connecting AI agents to premium data via MCP.

- **600M+ research products** via OpenAIRE
- **14M bibliographic records** via BnF
- **bioRxiv + medRxiv** preprint clusters
- Custom data clusters for enterprises

## Architecture

```
AI Agent (Claude/GPT/custom)
        ↓
    MCP Server
        ↓
┌───────┼───────┐
↓       ↓       ↓
OpenAIRE bioRxiv medRxiv
```

## MCP Tools (7 per cluster)

1. `datacluster_list_datasets`
2. `datacluster_get_dataset`
3. `datacluster_keyword_search`
4. `datacluster_vector_search_chunks`
5. `datacluster_get_entry_content`
6. `datacluster_get_entry_documents`
7. `datacluster_get_entry_file`

## Models Used

**Primary: Claude (Anthropic)**
- Integration via claude.ai, Claude Code, Claude Desktop
- Claude Agent SDK for hackathon
- OAuth authentication
- 29 read-only tools for OpenAIRE connector

Also supports: GPT-4, Mistral, Copilot, custom agents

## Key Design Decisions

- **Data never leaves your servers** (sovereign infrastructure)
- **No AI training** — inference only, architecture-enforced
- **EU-native** — GDPR, HIPAA, ISO 27001 compliant
- **Per-query metering** — you set the price
- **OAuth + API tokens** for authentication

## How Pāṭala Changes This

Alien gives agents: **current evidence**
Pāṭala gives agents: **maintainable knowledge**

```
Alien: "What does the source say NOW?"
Pāṭala: "Does what you concluded before still follow?"
```

Alien's value: access + provenance + sovereignty
Pāṭala's value: continuity + freshness + auditability

## Cost Implication

Alien uses Claude. Claude costs money per query.

Without Pāṭala: rerun everything on each update
With Pāṭala: only recompute affected conclusions

At 100 agents × 10 analyses/day:
- Without: $172K-$859K/year
- With Pāṭala: $57K-$283K/year
- Savings: $115K-$575K/year

But the real value isn't compute savings — it's correctness.
