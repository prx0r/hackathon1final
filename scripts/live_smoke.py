#!/usr/bin/env python3
"""Optional live OpenAIRE smoke test.

This does not mutate a workspace and is intentionally excluded from the deterministic
build certificate. It verifies current endpoint reachability and response normalization.
"""
from __future__ import annotations

from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import json
from patala_research_ci.model import QuerySpec
from patala_research_ci.openaire import OpenAIREStack


def main() -> int:
    stack = OpenAIREStack()
    spec = QuerySpec(entity="research-products", search="open science", filters={"type": "software"}, page_size=3)
    result = stack.fetch(spec)
    print(json.dumps({
        "status": result.status,
        "error": result.error,
        "request_urls": result.request_urls,
        "items": len(result.items),
        "sample": result.items[:1],
    }, indent=2, ensure_ascii=False))
    return 0 if result.status in {"OK", "PARTIAL"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
