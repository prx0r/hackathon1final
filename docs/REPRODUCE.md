# Reproduce

## Requirements

- Python 3.10+
- httpx (only dependency)

## Run the demo

```bash
python3 -m patala_research_ci.cli demo
```

## Run all tests

```bash
python3 -m unittest discover -s tests -v
```

## Run the release gate

```bash
python3 scripts/verify_release.py
```

## Live OpenAIRE query

```bash
python3 scripts/live_smoke.py
```

## What you can verify offline

- 33 tests pass
- Deterministic demo produces identical output
- Build certificate hashes match artifact set
- Ledger integrity verified
- Live Alien trace included (synthetic:false)
