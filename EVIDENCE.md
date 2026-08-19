# Aletheia — Evidence Model

## Four kinds of evidence

Aletheia distinguishes four kinds of evidence, each proving something different:

| Kind | What it proves | Example |
|------|---------------|---------|
| **Unit test** | Local policy/signature logic works | Test that SHA-256 produces correct hash |
| **Deterministic fixture** | Before/after produces same diff | Same 10 records → same impact report |
| **Graph roundtrip** | HydraDB executes real queries | OpenCypher write/read succeeds |
| **Certification gate** | Full HydraDB + algo.MSpaths + Prometheus | Docker container runs, all checks pass |

## The invariant

A conclusion is `VERIFIED_CURRENT` only when:
1. A PASS receipt exists from an authorized verifier
2. The receipt was signed by a known key
3. The receipt references a real invocation
4. The invocation references real evidence
5. The graph roundtrip succeeds

## Anti-cheat rules

```
SOURCE FAILURE ≠ ZERO RESULTS
PARTIAL SOURCE ≠ COMPLETE RESULT SET
COSMETIC CHANGE ≠ MATERIAL CHANGE
AGENT SAYS "FIXED" ≠ PROVEN RESOLUTION
HTTP 200 ≠ SUCCESS
```

## Certification levels

| Level | What passes | What it proves |
|-------|------------|----------------|
| Static | Unit tests | Policy logic works |
| Fixture | Deterministic demo | Same input → same output |
| Live | HydraDB graph ops | Real graph execution |
| Certified | Full gate | HydraDB + algo.MSpaths + Prometheus + all tests |
