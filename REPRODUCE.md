# Aletheia — Reproduce

## Requirements

- Python 3.10+
- httpx (only dependency)

## Deterministic demo

```bash
python3 -m aletheia.cli demo
```

## Live OpenAIRE query

```bash
python3 scripts/live_smoke.py
```

## Run all tests

```bash
python3 -m unittest discover -s tests -v
```

## Certification gate

```bash
python3 scripts/verify_release.py
```

This runs:
1. Compile check
2. Unit tests
3. JSON schema validation
4. Deterministic demo
5. Ledger verification
6. Evidence hashing

## What you can verify offline

- 33 tests pass deterministically
- Demo produces identical output on every run
- Build certificate hashes match artifact set
- Ledger integrity verified
- Live Alien trace included
