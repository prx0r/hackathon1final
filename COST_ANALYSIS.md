# Cost Analysis: Full-Scale Extrapolation

## OpenAIRE v11.3.0 (Aug 4, 2026)

- 6.43M products added (+1.69%)
- 318.7M relations removed (IsCitedBy → Cites cleanup)
- 1.05M funding relations removed (-9.32%)
- 12.35M affiliations added (+3.19%)

## Alien MCP / Claude Cost Model

Per OpenAIRE search call (~11K tokens):
- Haiku:  $0.003
- Sonnet: $0.04
- Opus:   $0.20

Typical analysis (5 searches + synthesis):
- Sonnet: $0.29/analysis
- Opus:   $1.43/analysis

## Agent Scale (100 agents, 10 analyses/day, 50 conclusions each)

| Metric | Without Aletheia | With Aletheia (33%) | With Aletheia (10%) |
|--------|---------------|-------------------|-------------------|
| Reruns/year | 600,000 | 198,000 | 60,000 |
| Cost (Sonnet) | $171,720 | $56,668 | $17,172 |
| Cost (Opus) | $858,600 | $283,338 | $85,860 |
| Savings | — | $115,052 | $556,740 |

## The real cost isn't compute

It's wrong conclusions acted upon:
- Policy team uses stale dashboard
- Committee makes decision based on wrong data
- Cost: >>$100,000 per wrong decision
- Aletheia cost: ~$0.01 per check

## Key insight

Aletheia is not a compute optimizer. It's correctness infrastructure.

As agents scale: compute savings are significant, correctness guarantees are existential.
