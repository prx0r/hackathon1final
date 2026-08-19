# Aletheia — Reproduce

## Requirements

- Python 3.10+
- httpx (only dependency)

## Deterministic demo (no Docker)

```bash
python3 -m aletheia.cli demo
```

## Live certification (Docker required)

```bash
./scripts/certify.sh
```

This runs:
1. HydraDB container startup
2. /readyz + /metrics health check
3. OpenCypher roundtrip
4. algo.MSpaths proof
5. Unit tests
6. Integration tests
7. False-success benchmark
8. Full demo
9. Evidence hashing
10. RUN_CERTIFICATE.json

## What you can verify offline

- 33 tests pass deterministically
- Demo produces identical output on every run
- Build certificate hashes match artifact set
- Ledger integrity verified
- Live Alien trace included
