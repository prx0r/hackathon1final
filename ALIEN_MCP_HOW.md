# Alien MCP — How It Works

*Source: OpenAIRE hackathon page*

## Architecture

```
Your question
      ↓
Claude (Agent SDK)
      ↓
┌─────┼─────┐
↓     ↓     ↓
OpenAIRE bioRxiv medRxiv
  MCP    MCP    MCP
```

## Three MCP servers

### OpenAIRE Research Graph
600M+ research products — search papers, explore citations, analyze author networks, discover datasets, track research trends, assess bibliometric impact.

### bioRxiv Data Cluster
Biology preprint repository — full-text search, vector similarity, structured metadata.

### medRxiv Data Cluster
Health sciences preprint repository — full-text search, vector similarity, structured metadata.

## How a query works

1. User types research question in natural language
2. Claude identifies intent and selects MCP tools
3. Tools called in parallel (OpenAIRE + bioRxiv simultaneously)
4. Large results delegated to subagents within context limits
5. Results synthesized into coherent answer with citations

## Capabilities

- Literature review
- Citation analysis
- Author landscape mapping
- Dataset discovery
- Bibliometric assessment
- Cross-domain discovery

## The gap Pāṭala fills

All of this produces **ephemeral answers**.

Agent asks → Claude queries → answer produced → answer stored.

When OpenAIRE changes, stored answers go stale. Nobody checks.

Pāṭala adds: **what happens to those answers tomorrow?**
