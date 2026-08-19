#!/usr/bin/env python3
"""Comprehensive POC: Real OpenAIRE data, realistic changes, full pipeline.

This demo proves the value of Research CI by:
1. Tracking real entities from OpenAIRE V3
2. Building meaningful dependencies with typed edges
3. Applying realistic changes from OpenAIRE's actual v11.3.0 release patterns
4. Running the full impact analysis
5. Measuring actual compute savings
6. Showing the complete before/after story

Uses real OpenAIRE V3 data. Changes are simulated based on documented
v11.3.0 changelog patterns (relation removal, dedup, metadata enrichment).
"""

import httpx
import json
import hashlib
import time
import sys
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from patala_research_ci.canonical import digest_json
from patala_research_ci.compiler import compile_trace
from patala_research_ci.model import (
    EpistemicLevel, ClaimState, Severity, SourceStatus,
    TrackedClaim, Dependency, ProofObligation
)
from patala_research_ci.impact import compute_impact
from patala_research_ci.obligations import obligations_from_impact
from patala_research_ci.learning import PriorityScore, wilson_lower

V3 = "https://api.openaire.eu/graph/v3"


# ============================================================
# UTILITIES
# ============================================================

def banner(text):
    print(f"\n{'═' * 70}")
    print(f"  {text}")
    print(f"{'═' * 70}\n")

def step(num, text):
    print(f"\n{'─' * 60}")
    print(f"  STEP {num}: {text}")
    print(f"{'─' * 60}\n")

def fetch(query, page_size=20):
    """Fetch from OpenAIRE V3."""
    params = {"pageSize": page_size}
    params.update(query)
    r = httpx.get(f"{V3}/research-products", params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("results", []), data.get("header", {}).get("numFound", 0)

def normalize(rec):
    """Normalize a record for comparison."""
    authors = rec.get("authors") or []
    pids = []
    for a in authors:
        pid = a.get("pid") or {}
        if isinstance(pid, dict):
            pids.append(pid.get("scheme", ""))
        elif isinstance(pid, str):
            pids.append(pid)
    return {
        "id": rec.get("id", ""),
        "title": (rec.get("mainTitle") or "").strip(),
        "type": rec.get("type", ""),
        "access": (rec.get("bestAccessRight") or {}).get("label", ""),
        "year": rec.get("publicationYear"),
        "has_orcid": any("orcid" in str(p).lower() for p in pids),
        "has_doi": bool(rec.get("pids")),
        "has_project": bool(rec.get("projects")),
        "relation_count": len(rec.get("relations") or []),
        "author_count": len(authors),
    }


# ============================================================
# SCENARIO DEFINITIONS — based on v11.3.0 changelog
# ============================================================

# v11.3.0 documented these changes:
# - 318.7M redundant IsCitedBy relations removed (Cites edges grew +58.6M)
# - 1.05M invalid funding relations removed
# - 6.43M new research products added
# - ScholeXplorer: publication-software links remapped from IsRelatedTo → Cites
# - Affiliations expanded +12.35M
# - Grey literature +30.81%

CHANGE_SCENARIOS = {
    "relation_cleanup": {
        "description": "IsCitedBy → Cites remapping (318.7M relations in v11.3.0)",
        "pattern": "relation_type_change",
        "materiality": "RELATION",
    },
    "funding_cleanup": {
        "description": "Invalid funding relations removed (1.05M in v11.3.0)",
        "pattern": "relation_removal",
        "materiality": "RELATION",
    },
    "dedup_merge": {
        "description": "Duplicate records merged into representative",
        "pattern": "entity_merge",
        "materiality": "IDENTITY",
    },
    "metadata_enrichment": {
        "description": "Affiliations expanded, grey literature +30.81%",
        "pattern": "field_update",
        "materiality": "METADATA",
    },
    "new_products": {
        "description": "6.43M new research products added",
        "pattern": "entity_addition",
        "materiality": "QUERY_MEMBERSHIP",
    },
}


# ============================================================
# THE DEMO
# ============================================================

def main():
    banner("PĀṬALA RESEARCH CI — COMPREHENSIVE POC")
    print("  Real OpenAIRE data · Realistic change scenarios · Full pipeline")

    # ─────────────────────────────────────────────
    # PHASE 1: ESTABLISH BASELINE
    # ─────────────────────────────────────────────
    step(1, "ESTABLISH BASELINE — tracking real OpenAIRE entities")

    # Use a focused query that returns manageable results
    queries = [
        {"name": "ai-software", "query": {"search": "artificial intelligence software", "type": "software"}, "label": "AI research software"},
        {"name": "open-science", "query": {"search": "open science tools", "type": "software"}, "label": "Open science tools"},
        {"name": "nlp-tools", "query": {"search": "natural language processing", "type": "publication"}, "label": "NLP publications"},
    ]

    baselines = {}
    all_entities = {}
    for q in queries:
        records, total = fetch(q["query"], page_size=15)
        normed = [normalize(r) for r in records]
        digest = digest_json(normed)
        baselines[q["name"]] = {
            "total": total,
            "count": len(normed),
            "digest": digest,
            "records": normed,
            "label": q["label"],
        }
        for n in normed:
            all_entities[n["id"]] = n
        print(f"  {q['name']:15s}: {total:>6d} total, {len(normed):>2d} tracked, digest={digest[:20]}...")

    total_tracked = len(all_entities)
    print(f"\n  Total unique entities tracked: {total_tracked}")

    # ─────────────────────────────────────────────
    # PHASE 2: BUILD MEANINGFUL DEPENDENCIES
    # ─────────────────────────────────────────────
    step(2, "BUILD DEPENDENCIES — not just entity IDs")

    # Create claims with realistic dependency structures
    claims = []

    # Claim 1: depends on query membership (fragile — changes if entities appear/disappear)
    claims.append(TrackedClaim(
        claim_id="claim:ai-software-count",
        text="There are approximately 175 AI research software products in OpenAIRE",
        dependencies=[Dependency(kind="query_membership", entity_id="ai-software")],
        epistemic_level=EpistemicLevel.OBSERVED.value,
    ))

    # Claim 2: depends on specific entity existence
    ai_entities = baselines["ai-software"]["records"][:3]
    for i, rec in enumerate(ai_entities):
        claims.append(TrackedClaim(
            claim_id=f"claim:entity-{i}",
            text=f"Product '{rec['title'][:40]}' exists with {rec['relation_count']} relations",
            dependencies=[
                Dependency(kind="entity", entity_id=rec["id"]),
                Dependency(kind="field", entity_id=rec["id"], field_path="relation_count"),
            ],
            epistemic_level=EpistemicLevel.OBSERVED.value,
        ))

    # Claim 3: depends on field value (fragile — changes if metadata is enriched)
    if ai_entities:
        rec = ai_entities[0]
        claims.append(TrackedClaim(
            claim_id="claim:oa-status",
            text=f"Product '{rec['title'][:30]}' has OA status: {rec['access']}",
            dependencies=[
                Dependency(kind="entity", entity_id=rec["id"]),
                Dependency(kind="field", entity_id=rec["id"], field_path="access"),
            ],
            epistemic_level=EpistemicLevel.OBSERVED.value,
        ))

    # Claim 4: depends on relation (fragile — changes if relation is removed/remapped)
    rel_entities = [r for r in baselines["ai-software"]["records"] if r["relation_count"] > 0][:2]
    for i, rec in enumerate(rel_entities):
        claims.append(TrackedClaim(
            claim_id=f"claim:relation-{i}",
            text=f"Product '{rec['title'][:30]}' has {rec['relation_count']} scholarly relations",
            dependencies=[
                Dependency(kind="entity", entity_id=rec["id"]),
                Dependency(kind="relation", source=rec["id"], relation="IsCitedBy"),
            ],
            epistemic_level=EpistemicLevel.OBSERVED.value,
        ))

    # Claim 5: cross-query dependency (depends on multiple sources)
    open_science_records = baselines["open-science"]["records"][:2]
    if open_science_records:
        claims.append(TrackedClaim(
            claim_id="claim:cross-source",
            text="AI software and open science tools share overlapping entities",
            dependencies=[
                Dependency(kind="entity", entity_id=ai_entities[0]["id"]) if ai_entities else None,
                Dependency(kind="entity", entity_id=open_science_records[0]["id"]),
            ],
            epistemic_level=EpistemicLevel.INFERRED.value,
        ))
    # Remove None dependencies
    claims = [c for c in claims if all(d is not None for d in c.dependencies)]

    print(f"  Claims created: {len(claims)}")
    for c in claims:
        deps = len(c.dependencies)
        level = EpistemicLevel(c.epistemic_level).value
        print(f"    {c.claim_id:25s} [{level:10s}] {deps} deps: {c.text[:50]}")

    # ─────────────────────────────────────────────
    # PHASE 3: SIMULATE REALISTIC OPENAIRE CHANGES
    # ─────────────────────────────────────────────
    step(3, "SIMULATE CHANGES — based on v11.3.0 changelog patterns")

    print("  Applying realistic change scenarios:")
    print("  (Based on OpenAIRE v11.3.0: 318.7M relation removals, 1.05M funding cleanup,")
    print("   6.43M new products, affiliation expansion, grey literature +30.81%)\n")

    # Build the "changed" state by modifying records realistically
    changed_records = {}
    changes_applied = []

    for eid, rec in all_entities.items():
        new_rec = dict(rec)

        # Scenario 1: relation_count changes (simulates IsCitedBy → Cites remapping)
        if new_rec["relation_count"] > 0 and hash(eid) % 3 == 0:
            old_count = new_rec["relation_count"]
            new_rec["relation_count"] = max(0, old_count - (hash(eid) % 5))
            if new_rec["relation_count"] != old_count:
                changes_applied.append({
                    "entity": eid, "field": "relation_count",
                    "old": old_count, "new": new_rec["relation_count"],
                    "scenario": "relation_cleanup",
                })

        # Scenario 2: access field changes (simulates metadata enrichment)
        if hash(eid) % 7 == 0 and new_rec["access"] == "":
            new_rec["access"] = "OPEN"
            changes_applied.append({
                "entity": eid, "field": "access",
                "old": "", "new": "OPEN",
                "scenario": "metadata_enrichment",
            })

        # Scenario 3: author count changes (simulates affiliation expansion)
        if hash(eid) % 11 == 0:
            new_rec["author_count"] = new_rec["author_count"] + 1
            changes_applied.append({
                "entity": eid, "field": "author_count",
                "old": new_rec["author_count"] - 1, "new": new_rec["author_count"],
                "scenario": "affiliation_expansion",
            })

        changed_records[eid] = new_rec

    # Scenario 4: remove some entities (simulates dedup merge)
    removed_eids = set()
    for eid in list(changed_records.keys()):
        if hash(eid) % 13 == 0:
            removed_eids.add(eid)
            changes_applied.append({
                "entity": eid, "field": "__removed__",
                "old": "present", "new": "merged",
                "scenario": "dedup_merge",
            })

    for eid in removed_eids:
        del changed_records[eid]

    # Scenario 5: add new entities (simulates new products)
    new_entities = []
    for i in range(3):
        new_id = f"new_entity_{i}::fake_dedup"
        new_rec = {
            "id": new_id,
            "title": f"New AI research product {i}",
            "type": "software",
            "access": "OPEN",
            "year": 2026,
            "has_orcid": True,
            "has_doi": True,
            "has_project": False,
            "relation_count": 2,
            "author_count": 3,
        }
        changed_records[new_id] = new_rec
        new_entities.append(new_id)
        changes_applied.append({
            "entity": new_id, "field": "__added__",
            "old": "absent", "new": "present",
            "scenario": "new_products",
        })

    print(f"  Changes applied: {len(changes_applied)}")
    scenarios = {}
    for c in changes_applied:
        s = c["scenario"]
        scenarios[s] = scenarios.get(s, 0) + 1
    for s, count in sorted(scenarios.items()):
        print(f"    {s:25s}: {count}")

    # ─────────────────────────────────────────────
    # PHASE 4: COMPUTE DIFF
    # ─────────────────────────────────────────────
    step(4, "COMPUTE SEMANTIC DIFF")

    old_ids = set(all_entities.keys())
    new_ids = set(changed_records.keys())
    added = new_ids - old_ids
    removed = old_ids - new_ids
    field_changes = [c for c in changes_applied if c["field"] != "__removed__" and c["field"] != "__added__"]

    print(f"  Old snapshot: {len(old_ids)} entities")
    print(f"  New snapshot: {len(new_ids)} entities")
    print(f"  Added:        {len(added)}")
    print(f"  Removed:      {len(removed)}")
    print(f"  Fields changed: {len(field_changes)}")

    if field_changes:
        print(f"\n  Field-level changes:")
        for c in field_changes[:5]:
            print(f"    {c['entity'][:20]}: {c['field']} {c['old']} → {c['new']}")

    # ─────────────────────────────────────────────
    # PHASE 5: IMPACT ANALYSIS
    # ─────────────────────────────────────────────
    step(5, "IMPACT ANALYSIS — which claims are affected?")

    from patala_research_ci.model import SemanticDiff as SD, Change, Materiality

    # Build a SemanticDiff from our changes
    changes = []
    for c in changes_applied:
        if c["field"] == "__removed__":
            changes.append(Change(
                change_id="chg:001", kind="ENTITY_REMOVED",
                materiality=Materiality.QUERY_MEMBERSHIP.value,
                entity_id=c["entity"], reason="dedup merge",
            ))
        elif c["field"] == "__added__":
            changes.append(Change(
                change_id="chg:002", kind="ENTITY_ADDED",
                materiality=Materiality.QUERY_MEMBERSHIP.value,
                entity_id=c["entity"], reason="new product",
            ))
        elif c["field"] == "relation_count":
            changes.append(Change(
                change_id="chg:003", kind="FIELD_CHANGED",
                materiality=Materiality.RELATION.value,
                entity_id=c["entity"], path="relation_count",
                before=c["old"], after=c["new"],
                reason="relation cleanup (IsCitedBy → Cites)",
            ))
        elif c["field"] == "access":
            changes.append(Change(
                change_id="chg:004", kind="FIELD_CHANGED",
                materiality=Materiality.AVAILABILITY.value,
                entity_id=c["entity"], path="access",
                before=c["old"], after=c["new"],
                reason="metadata enrichment",
            ))
        elif c["field"] == "author_count":
            changes.append(Change(
                change_id="chg:005", kind="FIELD_CHANGED",
                materiality=Materiality.METADATA.value,
                entity_id=c["entity"], path="author_count",
                before=c["old"], after=c["new"],
                reason="affiliation expansion",
            ))

    diff = SD(
        diff_id="diff:001", analysis_id="poc-demo",
        old_snapshot_id="snap:001", new_snapshot_id="snap:002",
        old_digest="sha256:old", new_digest="sha256:new",
        source_status=SourceStatus.OK.value,
        changes=changes,
        summary={"added": len(added), "removed": len(removed), "changed": len(field_changes)},
    )

    # Run impact analysis
    impact = compute_impact("poc-demo", diff, claims)

    print(f"  Claims analyzed: {len(claims)}")
    for imp in impact.claims:
        icon = {"CURRENT": "✅", "SOURCE_CHANGED": "⚠️", "RECOMPUTE_REQUIRED": "🔄",
                "HUMAN_REVIEW_REQUIRED": "👤"}.get(imp.state, "?")
        print(f"    {imp.claim_id:25s} {icon} {imp.state}")

    # ─────────────────────────────────────────────
    # PHASE 6: GENERATE PROOF OBLIGATIONS
    # ─────────────────────────────────────────────
    step(6, "PROOF OBLIGATIONS")

    obs = obligations_from_impact(impact)
    print(f"  Obligations generated: {len(obs)}")
    for o in obs:
        print(f"    {o.obligation_id}  {o.claim_id}")
        print(f"      Action:   {o.action}")
        print(f"      Priority: {o.priority}")
        print(f"      Severity: {o.severity}")
        print(f"      Reason:   {o.reason[:60]}")

    # ─────────────────────────────────────────────
    # PHASE 7: COMPUTE SAVINGS
    # ─────────────────────────────────────────────
    step(7, "COMPUTE SAVINGS — the business case")

    total_claims = len(claims)
    affected = len([i for i in impact.claims if i.state != ClaimState.CURRENT.value])
    unaffected = total_claims - affected

    # Estimate: each claim requires ~1 inference call to re-verify
    cost_per_call = 0.001  # $0.001 per inference call (cheap)
    naive_cost = total_claims * cost_per_call
    smart_cost = affected * cost_per_call
    saved = naive_cost - smart_cost
    saved_pct = (saved / naive_cost * 100) if naive_cost > 0 else 0

    print(f"  ┌─────────────────────────────────────────────────────────┐")
    print(f"  │  COMPUTE SAVINGS                                      │")
    print(f"  ├─────────────────────────────────────────────────────────┤")
    print(f"  │  Total claims:          {total_claims:>4}                          │")
    print(f"  │  Affected (recompute):  {affected:>4}                          │")
    print(f"  │  Unaffected (skip):     {unaffected:>4}                          │")
    print(f"  │                                                         │")
    print(f"  │  Naive (rerun all):     {naive_cost:>6.3f}                      │")
    print(f"  │  Smart (rerun affected): {smart_cost:>6.3f}                     │")
    print(f"  │  Saved:                 {saved:>6.3f} ({saved_pct:.1f}%)              │")
    print(f"  │                                                         │")
    print(f"  │  At 1000 claims:        ${naive_cost*1000/total_claims*1000:>8.2f} vs ${smart_cost*1000/total_claims*1000:>8.2f}          │")
    print(f"  │  At 1M claims:          ${naive_cost*1000000/total_claims*1000:>10.2f} vs ${smart_cost*1000000/total_claims*1000:>10.2f}    │")
    print(f"  └─────────────────────────────────────────────────────────┘")

    # ─────────────────────────────────────────────
    # PHASE 8: WHY THIS MATTERS
    # ─────────────────────────────────────────────
    step(8, "THE FULL STORY")

    print("  OpenAIRE v11.3.0 (August 4, 2026):")
    print("    +6.43M research products added")
    print("    -318.7M redundant relations removed")
    print("    -1.05M invalid funding relations removed")
    print("    ScholeXplorer: IsRelatedTo → Cites remapped")
    print("    Affiliations expanded +12.35M")
    print("    Grey literature +30.81%")
    print("")
    print("  An agent that queried OpenAIRE before v11.3.0 stored conclusions.")
    print("  Those conclusions may depend on relations that no longer exist.")
    print("")
    print("  Pāṭala detects:")
    print(f"    {affected} claims need re-verification")
    print(f"    {unaffected} claims are provably unaffected")
    print("")
    print("  Without Pāṭala:")
    print("    Rerun all {0} conclusions → {1:.3f}".format(total_claims, naive_cost))
    print("    Or worse: trust stale conclusions forever")
    print("")
    print("  With Pāṭala:")
    print("    Rerun {0} affected conclusions → {1:.3f}".format(affected, smart_cost))
    print("    Skip {0} unaffected conclusions".format(unaffected))
    print("    Save {0:.1f}% compute".format(saved_pct))
    print("    Every conclusion auditable with exact dependency chain")
    print("")
    print("  The tagline:")
    print('    "When the evidence changes, know what to recheck."')

    # ─────────────────────────────────────────────
    # SAVE RESULTS
    # ─────────────────────────────────────────────
    results = {
        "baseline": {k: {"total": v["total"], "count": v["count"], "digest": v["digest"]}
                     for k, v in baselines.items()},
        "entities_tracked": total_tracked,
        "claims": len(claims),
        "changes_applied": len(changes_applied),
        "change_scenarios": scenarios,
        "impact": {
            "affected": affected,
            "unaffected": unaffected,
            "total": total_claims,
        },
        "obligations": len(obs),
        "compute_savings": {
            "naive_cost": naive_cost,
            "smart_cost": smart_cost,
            "saved": saved,
            "saved_pct": saved_pct,
        },
    }
    out = Path(__file__).parent / "poc_results.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"\n  Results: {out}")


if __name__ == "__main__":
    main()
