# Pāṭala Research CI

**Continuous Verification for Agentic Science**

> OpenAIRE tells an agent what research says now. Pāṭala tells it whether what the agent concluded before still follows.

---

## The problem

OpenAIRE has **386M+ research products**. Its August 2026 release added 6.43M and removed **318.7M redundant relations** in one update.

An agent that concluded something based on those relations is now wrong. Nobody told it.

Alien Intelligence makes OpenAIRE agent-accessible. But a derived conclusion doesn't automatically become current when its source does.

## The solution

Pāṭala records which OpenAIRE observations a conclusion depends on. When the graph changes, it computes blast radius and emits proof obligations for affected conclusions only.

```
observation → derived conclusion → explicit dependency
                                          ↓
                                source changes
                                          ↓
                                blast radius computed
                                          ↓
                      affected: PROOF OBLIGATION
                    unaffected: NO ACTION NEEDED
```

## Quick start

```bash
pip install httpx

# Track an analysis
python3 -m patala_research_ci.cli track \
  --id my-analysis \
  --title "AI research software" \
  --search "artificial intelligence software" \
  --entity research-products

# Verify against current state
python3 -m patala_research_ci.cli verify my-analysis

# Import an Alien MCP trace
python3 -m patala_research_ci.cli mcp-import \
  artifacts/alien_mcp_trace.live.json --bind my-analysis

# Run the deterministic demo
python3 -m patala_research_ci.cli demo

# Check ledger integrity
python3 -m patala_research_ci.cli verify-ledger
```

## Architecture

```
Alien/OpenAIRE MCP → trace → observations → dependencies
                                                    ↓
                                        OpenAIRE state changes
                                                    ↓
                                         semantic diff + impact
                                                    ↓
                                         proof obligations
                                                    ↓
                                         verification receipts
```

## Invariants

```
SOURCE FAILURE ≠ ZERO RESULTS
PARTIAL SOURCE ≠ COMPLETE RESULT SET
COSMETIC CHANGE ≠ MATERIAL CHANGE
UPSTREAM CHANGE ≠ CONCLUSION FALSE
AGENT SAYS "FIXED" ≠ PROVEN RESOLUTION
```

## License

MIT (code), CC-BY 4.0 (documentation)
