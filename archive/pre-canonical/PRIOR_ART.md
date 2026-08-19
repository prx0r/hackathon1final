# Prior Art

## What exists

| System | What it does | What it doesn't |
|--------|-------------|-----------------|
| OpenAIRE Graph | 386M products, relations, entities | Doesn't know what YOU concluded |
| Alien MCP | Agent-access to OpenAIRE | Doesn't track derived state |
| TerminusDB | Graph versioning | Generic, not agent-aware |
| Graphiti | Agent memory graph | Doesn't do dependency invalidation |
| HUKA | Query provenance in dynamic KGs | Academic, not production |

## What we don't claim

- We don't claim to invent graph versioning (TerminusDB exists)
- We don't claim to invent provenance (W3C PROV-O exists)
- We don't claim to invent MCP (Alien already does it well)
- We don't claim to invent dependency tracking (build systems do it)

## What is novel

The end-to-end loop: MCP evidence → explicit dependencies → semantic change → blast radius → proof obligation → verification receipt. No existing system combines all six.
