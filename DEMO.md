# Aletheia judge demo — 90 seconds

## Goal

Demonstrate one thing: **when scholarly infrastructure changes, Aletheia distinguishes changes that matter to an agent's remembered conclusion from changes that do not.**

## 0:00–0:12 — Hook

Show three saved research conclusions, all green.

> “This agent used OpenAIRE to build these conclusions yesterday. OpenAIRE improves continuously. Which of these answers still deserve to be trusted today?”

Do not explain Merkle trees, RO-Crate, frozen plans, or the full internal schema here.

## 0:12–0:25 — Agent evidence

Show the bundled Alien/OpenAIRE trace or a live Alien query.

> “Alien gives the agent structured OpenAIRE evidence. Aletheia binds the derived conclusions to the exact entities, fields, relations and query membership they used.”

If a live Alien session is available, show only one or two calls. Do not spend the video scrolling through all 11 calls.

## 0:25–0:48 — Three upstream changes

Run:

```bash
python -m patala_research_ci --workspace /tmp/aletheia-demo demo
```

Narrate the fixture:

1. a title was normalized;
2. `IsCitedBy(A,B)` became `Cites(B,A)` — the same scholarly proposition represented on the active side;
3. one genuine dataset-support relation disappeared, and a new product entered the tracked query.

> “A raw JSON diff sees noise. Aletheia compares the meaning.”

## 0:48–1:05 — Blast radius

Point to the result:

```text
Dataset coverage   RECOMPUTE REQUIRED
Citation path      CURRENT
Access-right claim CURRENT
```

> “Exactly one conclusion needs work. The inverse citation migration is canonicalized away, and the unrelated title change cannot stale a claim that never depended on the title.”

## 1:05–1:20 — Revalidation

Show the dataset calculation:

```text
baseline 2 / 3 = 66.7%  → supported
current  1 / 4 = 25.0%  → unsupported
```

> “The affected claim gets a frozen proof obligation. The computable check reruns and produces a verification receipt. The conclusion changes because the evidence changed—not because an LLM guessed that it did.”

## 1:20–1:30 — Close

Show the three claim cards again: two green, one updated.

> **“OpenAIRE makes scholarly knowledge machine-actionable. Alien makes agents operational. Aletheia makes autonomous knowledge maintainable.”**

### Backup line

> “Alien tells an agent what OpenAIRE says now. Aletheia tells it which things it learned before still follow.”
