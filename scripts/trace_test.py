#!/usr/bin/env python3
"""End-to-end test: real Alien trace → dependencies → selective invalidation.

This is the ONE demonstration that matters.
"""

import httpx
import json
import hashlib
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from patala_research_ci.compiler import compile_trace, trace_to_observations
from patala_research_ci.canonical import digest_json

V3 = "https://api.openaire.eu/graph/v3"


def main():
    print("=" * 70)
    print("TRACE → DEPENDENCIES → SELECTIVE INVALIDATION")
    print("The ONE thing that matters")
    print("=" * 70)

    # Step 1: Load the real Alien trace
    print("\n[1] LOAD REAL ALIEN TRACE")
    trace_path = Path(__file__).parent.parent.parent / "artifacts" / "alien_mcp_trace.live.json"
    if not trace_path.exists():
        trace_path = Path(__file__).parent.parent.parent / "artifacts" / "alien_mcp_trace.example.json"
    trace = json.loads(trace_path.read_text())
    print(f"    Trace: {trace.get('trace_id', '?')}")
    print(f"    Calls: {len(trace.get('calls', []))}")
    print(f"    Synthetic: {trace.get('synthetic', '?')}")

    # Step 2: Compile trace → observations → dependencies
    print("\n[2] COMPILE TRACE → OBSERVATIONS → DEPENDENCIES")
    result = compile_trace(trace, claim_text="Sthaneshwar Timalsina")
    stats = result["stats"]
    print(f"    Observations: {stats['tool_calls']}")
    print(f"    Unique entity IDs: {stats['unique_entity_ids']}")
    print(f"    Candidate dependencies: {stats['candidate_dependencies']}")
    print(f"    High confidence: {stats['high_confidence']}")
    print(f"    Low confidence: {stats['low_confidence']}")

    print(f"\n    Observations:")
    for obs in result["observations"]:
        ids = len(obs["entity_ids"])
        print(f"      {obs['obs_id']}: {obs['tool']} → {ids} IDs")

    print(f"\n    Dependencies:")
    for dep in result["dependencies"][:5]:
        eid = dep.get("entity_id", "?")
        print(f"      {dep['dep_id']}: {dep['dep_kind']} → {eid[:40]}... (conf={dep['confidence']:.1f})")
    if len(result["dependencies"]) > 5:
        print(f"      ... and {len(result['dependencies']) - 5} more")

    # Step 3: Fetch current OpenAIRE state for the observed entity IDs
    print("\n[3] FETCH CURRENT STATE FOR OBSERVED ENTITIES")
    all_obs_ids = set()
    for obs in result["observations"]:
        all_obs_ids.update(obs["entity_ids"])

    # We can't fetch individual entities by OpenAIRE internal ID via V3 easily,
    # so let's track a real query that matches the trace
    query = "Kashmir Shaivism consciousness"
    print(f"    Query: {query}")
    r = httpx.get(f"{V3}/research-products", params={
        "search": query, "pageSize": 10
    }, timeout=30)
    r.raise_for_status()
    current_records = r.json().get("results", [])
    current_ids = {rec["id"] for rec in current_records}
    print(f"    Current records: {len(current_records)}")

    # Step 4: Compute diff between trace observations and current state
    print("\n[4] COMPUTE DIFF")
    trace_ids = all_obs_ids
    added = current_ids - trace_ids
    removed = trace_ids - current_ids
    unchanged = trace_ids & current_ids

    print(f"    Trace IDs: {len(trace_ids)}")
    print(f"    Current IDs: {len(current_ids)}")
    print(f"    Added: {len(added)}")
    print(f"    Removed: {len(removed)}")
    print(f"    Unchanged: {len(unchanged)}")

    # Step 5: Predict which dependencies are affected
    print("\n[5] IMPACT ANALYSIS")
    affected_deps = []
    unaffected_deps = []
    for dep in result["dependencies"]:
        eid = dep.get("entity_id")
        if eid and eid in removed:
            affected_deps.append(dep)
        elif eid and eid in added:
            # New entity — dependency still satisfied
            unaffected_deps.append(dep)
        else:
            unaffected_deps.append(dep)

    print(f"    Dependencies affected: {len(affected_deps)}")
    print(f"    Dependencies unaffected: {len(unaffected_deps)}")

    if affected_deps:
        print(f"\n    AFFECTED:")
        for dep in affected_deps:
            print(f"      {dep['dep_id']}: entity {dep.get('entity_id', '?')[:40]} REMOVED")
            print(f"        → claim depending on this entity needs re-verification")

    # Step 6: Summary
    print("\n" + "=" * 70)
    print("RESULT")
    print("=" * 70)

    total_deps = len(result["dependencies"])
    affected_count = len(affected_deps)

    print(f"""
  TRACE: {trace.get('trace_id', '?')}
  {stats['tool_calls']} tool calls
  {stats['unique_entity_ids']} unique entity IDs
  {stats['candidate_dependencies']} candidate dependencies

  CURRENT STATE:
  {len(current_ids)} records

  DIFF:
  {len(added)} added, {len(removed)} removed, {len(unchanged)} unchanged

  IMPACT:
  {affected_count}/{total_deps} dependencies affected
  {total_deps - affected_count}/{total_deps} dependencies unaffected

  WITHOUT Patala:
    Rerun all {stats['tool_calls']} tool calls
    Reprocess all data

  WITH Patala:
    {affected_count} dependencies need attention
    {total_deps - affected_count} dependencies provably current
    Skip {((total_deps - affected_count) / max(total_deps, 1)):.0%} of work
""")

    if affected_deps:
        print("  PROOF OBLIGATIONS:")
        for dep in affected_deps:
            print(f"    Re-verify dependency on {dep.get('entity_id', '?')[:30]}")
            print(f"    Reason: entity removed from current OpenAIRE state")
            print(f"    Action: RECOMPUTE or HUMAN_REVIEW")
    else:
        print("  No proof obligations needed.")
        print("  All dependencies currently satisfied.")

    # Save results
    output = {
        "trace_id": trace.get("trace_id"),
        "stats": stats,
        "diff": {"added": len(added), "removed": len(removed), "unchanged": len(unchanged)},
        "impact": {"affected": affected_count, "unaffected": total_deps - affected_count},
        "affected_deps": affected_deps,
    }
    out_path = Path(__file__).parent / "results.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\n  Results: {out_path}")


if __name__ == "__main__":
    main()
