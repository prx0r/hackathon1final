# The Strongest Framing

*After reviewing OpenAIRE strategy, Alien engineering, and the full product stack.*

---

## The one-liner

> **Alien makes agent runs reliable. Aletheia makes their results remain reliable.**

---

## The architecture

```
TODAY:

OpenAIRE → Alien MCP → Agent → Answer

FUTURE WITH ALETHEIA:

OpenAIRE → Alien MCP → Agent → Derived Claim
                                         │
                                    Aletheia Receipt
                                         │
                                    dependencies
                                         │
                              source evolves over time
                                         │
                                    blast radius
                                         │
                                   revalidate
                                         │
                                    new receipt
```

---

## What each layer does

| Layer | What it solves |
|-------|---------------|
| **OpenAIRE** | Trusted scholarly intelligence substrate |
| **Alien** | Agent runtime: tools, orchestration, persistence, observability |
| **Aletheia** | Continuity: making derived knowledge maintainable after the run |

---

## The six problems this solves

1. **Agents persist conclusions** — conclusions outlive execution
2. **Multi-agent trust** — Agent B inherits Agent A's claims without knowing their status
3. **Graph evolves** — old conclusions depend on changed records
4. **Hybrid pipelines waste compute** — rerunning everything is expensive
5. **Research intelligence needs accountability** — policy/funding decisions must be inspectable
6. **Model changes propagate** — a bug in a model can invalidate specific derivations

---

## The pitch to OpenAIRE + Alien

> You are building infrastructure that lets autonomous agents use trusted scholarly knowledge.
>
> OpenAIRE gives agents a governed research-intelligence substrate. Alien gives them tools, orchestration, persistence and production execution.
>
> But autonomous agents create a new durable object: **the conclusion**.
>
> That conclusion may survive for months while the Graph, MCP semantics, models and surrounding evidence continue to evolve.
>
> **Aletheia extends your execution graph through time.**
>
> OpenAIRE remains the source of current intelligence. Alien remains the runtime for agents. Aletheia makes the knowledge those agents produce maintainable.

---

## The demo (2 minutes)

1. Agent queries OpenAIRE via Alien MCP (real trace)
2. Agent produces 3 conclusions with freshness receipts
3. OpenAIRE changes
4. 1 representational change → normalized away (semantic intelligence)
5. 1 irrelevant change → no impact (precision)
6. 1 meaningful relation change → exactly 1 conclusion flagged (value)
7. Agent selectively revalidates, new receipt issued

---

## The tagline

> **OpenAIRE makes knowledge machine-actionable.**
> **Alien makes agents operational.**
> **Aletheia makes autonomous knowledge maintainable.**
