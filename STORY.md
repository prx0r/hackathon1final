# The Story

## The question

OpenAIRE and Alien Intelligence have made scholarly intelligence directly accessible to autonomous agents. But what happens to agent conclusions when the evidence changes?

## The journey

We started by trying to build "Git for knowledge graphs." That was wrong — OpenAIRE already does versioning.

We then searched for the actual gap. OpenAIRE continuously validates the Graph. Alien makes it agent-accessible. But nobody tracks what agents derived from it.

The breakthrough: applying existing Aletheia primitives (append-only events, content hashing, blast-radius propagation) to this general problem.

## The insight

**Inference is becoming free. Knowing what remains justified is becoming scarce.**

OpenAIRE's August 2026 release removed 318.7M redundant relations. Any agent conclusion depending on those relations is now potentially wrong. Nobody told the agent.

Aletheia asks: "Did any of them matter to your research?"

## What others can reuse

- OpenAIRE V3 adapter with anti-cheat invariants
- MCP trace capture with credential redaction
- Dependency-aware impact analysis
- Proof obligations with frozen acceptance criteria
- Verification receipts with content addressing

The same protocol works with Crossref, DataCite, PubMed, OpenAlex, or any evolving data source.

## The tagline

> **When the evidence changes, know what to recheck.**
