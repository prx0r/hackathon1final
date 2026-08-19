# Aletheia — 90-Second Demo Script

## Setup

Run the deterministic demo (no Docker needed):

```bash
python3 -m aletheia.cli demo
```

Or the live version (Docker + HydraDB):

```bash
./scripts/certify.sh
```

## The script

```
0:00  "An AI agent used OpenAIRE to research software
      in artificial intelligence. It concluded there are
      175 products. That conclusion is stored in memory."

      [SCREEN: agent stores "175 products" with dependencies]

0:15  "OpenAIRE updated. 318 million relations were
      restructured. Some of the products the agent
      tracked are gone."

      [SCREEN: OpenAIRE changelog — 318.7M relations removed]

0:30  "Aletheia recorded which observations the agent
      used. It knows which conclusions depend on
      which records."

      [SCREEN: dependency graph showing 10 tracked entities]

0:45  "After the update, Aletheia checks each dependency.
      8 still present. 2 gone."

      [SCREEN: impact report]

      "4 conclusions unaffected — no action needed."
      "2 conclusions affected — proof obligation emitted."

1:00  "Without Aletheia: rerun everything.
      With Aletheia: rerun 2 out of 6."

      [SCREEN: compute savings]

1:15  "Alien makes research intelligence accessible.
      Aletheia makes what agents learn maintainable."

1:30  "When evidence changes, know what to recheck."
```

## What NOT to include

- No orchestration
- No cross-agent trust
- No learning mechanisms
- No future features
- No complexity beyond the 3-step loop

## Principle

**Demo = proof. Pitch = vision. Never mix them.**
