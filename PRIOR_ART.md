# Aletheia — Prior Art

## What exists

| System | What it does | Gap |
|--------|-------------|-----|
| OpenAIRE Graph | 386M products, relations | Doesn't track what YOU concluded |
| Alien MCP | Agent-access to OpenAIRE | Doesn't track derived state |
| HydraDB | Graph database for AI | No verification boundary |
| ToolGate (ACL 2026) | Trusted symbolic state | Pre/postconditions, not graph claims |
| ERC-8004 | Agent receipts | Validation concepts, not HydraDB-native |
| VPR | Verifiable intermediate rewards | Requires reliable oracles |

## What is novel

The join: turn verifier-gated transitions into durable, traversable shared graph state inside HydraDB, directly at the point where action recipes feed execution outcomes back into future reasoning.

Not graph versioning. Not provenance. Not MCP. The verification boundary at the point of state promotion.

## What we don't claim

- We don't claim to invent verification (ToolGate exists)
- We don't claim to invent receipts (ERC-8004 exists)
- We don't claim to invent graph databases (HydraDB exists)
- We claim: the join of verification + graph state + action routing is novel
