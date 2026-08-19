# Aletheia — Evidence Model

## Four kinds of evidence

| Kind | What it proves | Counts as proof? |
|------|---------------|-----------------|
| **Unit test** | Local policy/signature logic | No |
| **Deterministic fixture** | Same input → same output | Partly |
| **OpenAIRE V3 API** | Real graph data retrieved | Partly |
| **Certification gate** | All checks + ledger integrity | **Yes** |

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
| Live | OpenAIRE V3 API | Real graph data retrieved |
| Certified | All tests + ledger | Complete verification |
