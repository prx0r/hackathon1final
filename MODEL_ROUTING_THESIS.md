# Model Routing + Aletheia — The Deeper Architecture

*Why routing should be a consequence of Aletheia, not a replacement.*

---

## Alien is not Claude-only

Alien's terms list OpenAI, Google, Anthropic, Mistral, and Scaleway as LLM providers. Their infrastructure is explicitly multi-model.

The OpenAIRE reference app uses Claude Agent SDK because it's a "convenient mature agent harness," not because Claude is strategically required.

## What Alien already has

```
models ✓
tools ✓
data ✓
agents ✓
observability ✓
```

## What Alien doesn't publicly have

```
"Which computation deserves expensive intelligence?"
"Which result can be mechanically verified?"
"Which conclusion's correctness depends on this model choice?"
```

That's where Aletheia adds value.

---

## The routing insight

A normal router knows:

```
prompt, token count, model price, latency, benchmark score
```

Aletheia knows something more useful:

```
What is this operation trying to prove?
How important is it?
What downstream conclusions depend on it?
How uncertain is the evidence?
Can the result be deterministically checked?
What would constitute successful verification?
```

This enables **epistemic routing**: route compute according to consequences of being wrong.

---

## The routing formula

```python
risk = (
    claim_criticality
    * downstream_blast_radius
    * epistemic_uncertainty
    * source_uncertainty
    * verification_difficulty
)
```

Then:

```
risk < .15  → deterministic / tiny model
.15-.4      → cheap capable model
.4-.7       → stronger model
> .7        → frontier model + verification
critical    → frontier + independent review/human
```

---

## Speculative execution for reasoning

```
TRY CHEAP MODEL
      ↓
output
      ↓
Aletheia verification gate
      │
      ├── satisfies proof obligation → accept
      │
      └── cannot demonstrate adequacy → escalate
               ↓
          stronger model
               ↓
             verify
```

Cheap first. Expensive only when cheap result cannot satisfy proof.

---

## The OpenAIRE example

```
ProofObligation PO-17:
  "Dataset D supports conclusion C"
  Need: establish whether support relation still exists

Step 1: deterministic OpenAIRE lookup
  → cost: API call
  → if resolves: ✓ receipt

Step 2: cheap LLM examines structured metadata
  → if satisfies verifier: ✓ receipt

Step 3: frontier research model
  → if ambiguous: independent model / human
```

That's verification-aware computation routing.

---

## Multi-model auditability

A derived conclusion can have:

```
Claim C
├── source dependencies
│   ├── OpenAIRE entities
│   └── relations
└── computation provenance
     ├── model
     ├── model version
     ├── prompt/skill digest
     ├── MCP version
     ├── tool calls
     └── verification policy
```

Receipt says: derived from these observations, using these computational steps, passed these verification checks.

---

## The long-term thesis

```
SOURCE DEPENDENCIES    OpenAIRE, Crossref, datasets
TOOL DEPENDENCIES     MCP tool, query semantics, API schema
COMPUTATION DEPS      model, prompt, skill, code, algorithm
HUMAN DEPENDENCIES    review, adjudication, assertion
```

Changes to any of these trigger targeted verification.

Aletheia becomes the **epistemic control plane for agent computation**.

---

## The product stack

```
Alien: source → tool → execution
Aletheia: execution → claim → dependency → change → revalidation
Router: revalidation → cheapest sufficient computation
```

**Not a router. Routing is a consequence of Aletheia.**
