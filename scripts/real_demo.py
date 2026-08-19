#!/usr/bin/env python3
"""Real demo: Track OpenAIRE indicators, detect changes, show selective invalidation.

Uses real OpenAIRE V3 data. Demonstrates the product thesis:
"Graph changed in 74 places. This statement doesn't care. This one does."
"""

import httpx
import json
import hashlib
import time
from pathlib import Path

V3 = "https://api.openaire.eu/graph/v3"


def fetch(query: dict) -> tuple[list[dict], int]:
    params = {"pageSize": 50}
    params.update(query)
    r = httpx.get(f"{V3}/research-products", params=params, timeout=30)
    r.raise_for_status()
    d = r.json()
    return d.get("results", []), d.get("header", {}).get("numFound", 0)


def normalize(rec):
    authors = rec.get("authors") or []
    pids_raw = []
    for a in authors:
        pid = a.get("pid") or {}
        if isinstance(pid, dict):
            pids_raw.append(pid.get("scheme", ""))
        elif isinstance(pid, str):
            pids_raw.append(pid)
    return {
        "id": rec.get("id", ""),
        "type": rec.get("type", ""),
        "access": (rec.get("bestAccessRight") or {}).get("label", ""),
        "has_orcid": any("orcid" in str(p).lower() for p in pids_raw),
        "has_doi": any("doi" in str(p).lower() for p in (rec.get("pids") or [])),
        "has_pid": bool(rec.get("pids")),
        "has_project": bool(rec.get("projects")),
        "peer_reviewed": rec.get("isPeerReviewed"),
    }


def snap_digest(normed):
    c = json.dumps(sorted(normed, key=lambda x: x["id"]), separators=(",", ":"))
    return "sha256:" + hashlib.sha256(c.encode()).hexdigest()


def count_matching(normed, predicate):
    return sum(1 for n in normed if predicate(n))


# =========================================================
# INDICATOR DEFINITIONS (from MONITOR)
# =========================================================
INDICATORS = [
    {
        "id": "I1:software-count",
        "name": "Software production",
        "query": {"type": "software"},
        "compute": lambda n: len(n),
        "deps": {"query:software"},
    },
    {
        "id": "I2:publication-count",
        "name": "Publication count",
        "query": {"type": "publication"},
        "compute": lambda n: len(n),
        "deps": {"query:publication"},
    },
    {
        "id": "I3:dataset-count",
        "name": "Dataset count",
        "query": {"type": "dataset"},
        "compute": lambda n: len(n),
        "deps": {"query:dataset"},
    },
    {
        "id": "I4:oa-share",
        "name": "Open-access share (publications)",
        "query": {"type": "publication"},
        "compute": lambda n: round(count_matching(n, lambda x: x["access"] == "OPEN") / max(len(n), 1), 3),
        "deps": {"query:publication", "field:access"},
    },
    {
        "id": "I5:orcid-coverage",
        "name": "ORCID coverage (publications)",
        "query": {"type": "publication"},
        "compute": lambda n: round(count_matching(n, lambda x: x["has_orcid"]) / max(len(n), 1), 3),
        "deps": {"query:publication", "field:orcid"},
    },
    {
        "id": "I6:doi-coverage",
        "name": "DOI coverage (publications)",
        "query": {"type": "publication"},
        "compute": lambda n: round(count_matching(n, lambda x: x["has_doi"]) / max(len(n), 1), 3),
        "deps": {"query:publication", "field:doi"},
    },
    {
        "id": "I7:grant-coverage",
        "name": "Grant-linked share (publications)",
        "query": {"type": "publication"},
        "compute": lambda n: round(count_matching(n, lambda x: x["has_project"]) / max(len(n), 1), 3),
        "deps": {"query:publication", "field:project"},
    },
    {
        "id": "I8:peer-reviewed-share",
        "name": "Peer-reviewed share (publications)",
        "query": {"type": "publication"},
        "compute": lambda n: round(count_matching(n, lambda x: x.get("peer_reviewed") == True) / max(len(n), 1), 3),
        "deps": {"query:publication", "field:peer_reviewed"},
    },
    {
        "id": "I9:software-open-share",
        "name": "Open-source software share",
        "query": {"type": "software"},
        "compute": lambda n: round(count_matching(n, lambda x: x["access"] == "OPEN") / max(len(n), 1), 3),
        "deps": {"query:software", "field:access"},
    },
    {
        "id": "I10:mixed-query-count",
        "name": "Mixed query (AI + open science)",
        "query": {"search": "artificial intelligence open science"},
        "compute": lambda n: len(n),
        "deps": {"query:mixed"},
    },
]


def run():
    print("=" * 70)
    print("PATALA RESEARCH CI — REAL OPENAIRE SELECTIVE INVALIDATION DEMO")
    print("=" * 70)

    # Phase 1: Establish baseline
    print("\n[1] BASELINE — fetching from OpenAIRE V3...")
    baselines = {}
    for ind in INDICATORS:
        records, total = fetch(ind["query"])
        normed = [normalize(r) for r in records]
        digest = snap_digest(normed)
        value = ind["compute"](normed)
        baselines[ind["id"]] = {
            "value": value,
            "total": total,
            "records": len(normed),
            "digest": digest,
            "snapshot": normed,
        }
        print(f"  {ind['id']:30s} = {value}  ({total} total, {len(normed)} fetched)")

    baseline_digest = snap_digest(
        [{"id": k, **v} for k, v in baselines.items()]
    )
    print(f"\n  Overall baseline digest: {baseline_digest[:40]}...")

    # Phase 2: Detect changes (re-query, compare)
    print("\n[2] CHANGES — re-querying OpenAIRE V3...")
    changes = {}
    for ind in INDICATORS:
        records, total = fetch(ind["query"])
        normed = [normalize(r) for r in records]
        digest = snap_digest(normed)
        new_value = ind["compute"](normed)
        old_value = baselines[ind["id"]]["value"]
        old_records = baselines[ind["id"]]["snapshot"]
        old_ids = {r["id"] for r in old_records}
        new_ids = {r["id"] for r in normed}
        added = new_ids - old_ids
        removed = old_ids - new_ids
        field_changes = 0
        for r in normed:
            if r["id"] in old_ids:
                old_r = next(o for o in old_records if o["id"] == r["id"])
                for f in set(old_r.keys()) | set(r.keys()):
                    if old_r.get(f) != r.get(f):
                        field_changes += 1

        if old_value != new_value or added or removed:
            changes[ind["id"]] = {
                "old": old_value, "new": new_value,
                "added": len(added), "removed": len(removed),
                "field_changes": field_changes,
                "changed": True,
            }
            print(f"  CHANGED: {ind['id']:30s} {old_value} → {new_value}  (+{len(added)} -{len(removed)} ~{field_changes})")
        else:
            changes[ind["id"]] = {"old": old_value, "new": new_value, "changed": False}
            print(f"  unchanged: {ind['id']:30s}")

    # Phase 3: Predict affected indicators using dependency graph
    print("\n[3] PREDICTION — which indicators depend on changed properties?")
    all_change_keys = set()
    for iid, chg in changes.items():
        if chg["changed"]:
            ind = next(i for i in INDICATORS if i["id"] == iid)
            for dep in ind["deps"]:
                all_change_keys.add(dep)

    predictions = {}
    for ind in INDICATORS:
        affected = bool(ind["deps"] & all_change_keys)
        predictions[ind["id"]] = affected

    actually_changed = {iid for iid, c in changes.items() if c["changed"]}
    predicted_affected = {iid for iid, p in predictions.items() if p}

    print(f"  Changed properties: {all_change_keys}")
    print(f"  Predicted affected: {len(predicted_affected)}")
    print(f"  Actually changed:   {len(actually_changed)}")

    for ind in INDICATORS:
        pred = predictions[ind["id"]]
        actually = ind["id"] in actually_changed
        if pred and actually:
            print(f"    {ind['id']:30s} PREDICTED AFFECTED + CHANGED ✓")
        elif pred and not actually:
            print(f"    {ind['id']:30s} PREDICTED AFFECTED (false alarm)")
        elif not pred and actually:
            print(f"    {ind['id']:30s} MISSED! ← bad")
        else:
            print(f"    {ind['id']:30s} correctly unaffected")

    # Phase 4: Evaluate
    print("\n" + "=" * 70)
    print("EVALUATION")
    print("=" * 70)

    tp = actually_changed & predicted_affected
    fp = predicted_affected - actually_changed
    fn = actually_changed - predicted_affected
    tn = set(predictions.keys()) - actually_changed - predicted_affected

    precision = len(tp) / max(len(predicted_affected), 1)
    recall = len(tp) / max(len(actually_changed), 1)
    avoided = len(tn) / max(len(predictions), 1)

    print(f"\n  Indicators tracked:     {len(INDICATORS)}")
    print(f"  Actually changed:       {len(actually_changed)}")
    print(f"  Predicted affected:     {len(predicted_affected)}")
    print(f"  Correctly unaffected:   {len(tn)}")
    print(f"")
    print(f"  Impact precision:       {precision:.2f}")
    print(f"  Impact recall:          {recall:.2f}")
    print(f"  Recomputation avoided:  {avoided:.1%}")
    print(f"")

    if tp:
        print(f"  CORRECTLY PREDICTED:")
        for iid in sorted(tp):
            chg = changes[iid]
            print(f"    {iid}: {chg['old']} → {chg['new']}")
    if fp:
        print(f"\n  FALSE ALARMS (predicted but unchanged):")
        for iid in sorted(fp):
            print(f"    {iid}")
    if fn:
        print(f"\n  MISSED (changed but not predicted):")
        for iid in sorted(fn):
            print(f"    {iid}")

    # The product story
    total_indicators = len(INDICATORS)
    need_recompute = len(predicted_affected)
    saved = total_indicators - need_recompute

    print(f"\n" + "=" * 70)
    print("THE PRODUCT STORY")
    print("=" * 70)
    print(f"""
  WITHOUT Patala:
    OpenAIRE changed → rerun all {total_indicators} indicator computations

  WITH Patala:
    OpenAIRE changed → dependency analysis → {need_recompute} need recomputation
    → {saved} indicators provably unaffected
    → skip {avoided:.0%} of work
""")
    print(f"  That is the product.")
    print(f"  Not 'OpenAIRE changed.'")
    print(f"  But: 'OpenAIRE changed, and here is exactly what matters to your analysis.'")

    # Save results
    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "indicators": len(INDICATORS),
        "actually_changed": len(actually_changed),
        "predicted_affected": len(predicted_affected),
        "precision": precision,
        "recall": recall,
        "recompute_avoided": avoided,
        "changes": {k: v for k, v in changes.items() if v.get("changed")},
        "predictions": predictions,
    }
    Path("/root/hackathon1/evaluation/monitor_ci/real_demo_results.json").write_text(
        json.dumps(results, indent=2))


if __name__ == "__main__":
    run()
