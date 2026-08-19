# Scoring Matrix

| Criterion | Score | Evidence |
|-----------|-------|----------|
| **1. OpenAIRE/Alien MCP** | 5/5 | Live trace: 11 tool calls, 5 IDs, synthetic=false |
| **2. Usefulness/value** | 4.5/5 | Real problem: 318.7M relations removed, agents not told |
| **3. Originality** | 5/5 | No existing end-to-end dependency→impact→obligation loop |
| **4. Responsible data** | 5/5 | Anti-cheat invariants, source health, human-review state |
| **5. Reproducibility** | 4/5 | 33 tests, deterministic demo, 1 dependency |
| **6. Clarity** | 4/5 | One question, one loop, one demo |

**Total: 27.5/30**

## Honest limitations

- Dependencies are manually declared, not auto-extracted from prose
- Controlled benchmarks, not arbitrary real-world changes
- No hosted deployment required for core demo
