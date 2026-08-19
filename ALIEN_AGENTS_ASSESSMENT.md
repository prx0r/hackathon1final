# Alien's Own Agents — validate the problem

*Source: the-alien-club GitHub repos*

---

## ai-sre (22 stars, TypeScript)

**What it does:**
- Receives SigNoz alerts via webhook
- Investigates autonomously using kubectl and traces
- Auto-fixes safe issues (pod restarts, workflow clears)
- Escalates to CTO on Slack with full context
- Sub-agent delegation pattern
- **Incident memory via SQLite**
- **Runs unattended for DAYS/WEEKS**

**MCP tools used:**
- SigNoz (logs, traces, metrics)
- kubectl (Kubernetes operations)
- Slack (communication)
- Trivy (security scanning)

**From their CLAUDE.md:**
> "YOUR CONTEXT WINDOW IS YOUR LIFELINE. If it fills up, you die and must restart."
> "NEVER run kubectl yourself. Always delegate to sub-agents."

---

## This validates Aletheia

Alien's OWN agent:
- Persists memory (SQLite) ✅
- Runs for days/weeks ✅
- Delegates to sub-agents ✅
- Has context window management ✅

**If that agent's underlying data changes:**
- SigNoz metrics change → alert conclusions stale
- kubectl state changes → fix conclusions stale
- Slack context changes → escalation conclusions stale

**Aletheia would track which conclusions depend on which MCP data.**

---

## Also found

- `mcp-evaluation-harness` — Claude-based MCP evaluation harness
- `claude-marketplace` — Claude plugins marketplace (OpenAIRE plugin lives here)
- `claude-workflows` — Team claude workflow templates

---

## Conclusion

Alien is building agents that persist conclusions.
Those conclusions can go stale.
Aletheia solves that.
