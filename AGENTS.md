# AGENTS.md — Pāṭala Research CI

*2026-08-19 · Governing rules for this project.*

---

## THE ONE RULE

> **Nothing is "real" because a file exists. It is real when a reproducible pipeline, clean input, verifiable output, and honest gate show it does what it claims.**

A number with no content-addressed run record is theater.

---

## WHAT THIS PROJECT IS

Pāṭala Research CI is a continuous verification layer for research built on evolving scholarly knowledge graphs. It tracks which OpenAIRE observations support which conclusions, detects when observations change, and emits proof obligations for affected conclusions.

## HOW TO RUN

```bash
# Track
python3 -m patala_research_ci.cli track --id test --search "AI software"

# Verify
python3 -m patala_research_ci.cli verify test

# Demo
python3 -m patala_research_ci.cli demo

# Tests
python3 -m unittest discover -s tests -v

# Release gate
python3 scripts/verify_release.py
```

## THE GATE

```bash
python3 -m compileall -q patala_research_ci
python3 -m unittest discover -s tests -v
python3 scripts/verify_release.py
```

All must pass before claiming done.

## BOX RULES

- Never sleep to wait
- Never pkill — find exact PID
- RAM is scarcest resource
- Reuse, don't rebuild
