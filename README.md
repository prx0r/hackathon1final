# Aletheia

**Continuous Verification for Agentic Science**

> When evidence changes, know what to recheck.

---

## What it is

Aletheia tracks which OpenAIRE observations a conclusion depends on. When the graph changes, it computes blast radius and emits proof obligations for affected conclusions only.

## How it works (90-second demo)

```
0:00  "An AI agent used OpenAIRE to research software
      in artificial intelligence. It concluded there are
      175 products. That conclusion is stored in memory."

      [Show: agent stores "175 products"]

0:15  "OpenAIRE updated. 318 million relations were
      restructured. Some of the products the agent
      tracked are gone."

      [Show: OpenAIRE changelog numbers]

0:30  "Aletheia recorded which observations the agent
      used. It knows which conclusions depend on
      which records."

      [Show: dependency graph — 19 dependencies]

0:45  "After the update, Aletheia checks each dependency.
      11 still present. 8 gone."

      [Show: impact report]

      "4 conclusions unaffected — no action needed."
      "2 conclusions affected — proof obligation emitted."

1:00  "Without Aletheia: rerun everything.
      With Aletheia: rerun 2 out of 6."

      [Show: compute savings]

1:15  "Alien makes research intelligence accessible.
      Aletheia makes what agents learn maintainable."

1:30  "When evidence changes, know what to recheck."
```

## The pitch (3 sentences)

> OpenAIRE tells agents what research says now.
> Aletheia tells them whether what they concluded before still follows.
> When evidence changes, know what to recheck.

## Why "Aletheia"

Aletheia (ἀλήθεια) is the Greek concept of truth as unconcealment — truth that has been hidden becoming revealed.

The system doesn't claim to know what's true. It reveals which conclusions have become disconnected from their evidence.

That's exactly what it does.

> **Aletheia: truth unconcealed.**
