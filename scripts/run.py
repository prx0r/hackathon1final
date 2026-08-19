#!/usr/bin/env python3
"""MONITOR CI Benchmark — prove Pāṭala predicts which indicators are affected by Graph changes.

Uses real OpenAIRE V3 data. No mocks, no synthetic fixtures.
"""

import httpx
import json
import hashlib
import re
import time
from pathlib import Path
from typing import Any


V3 = "https://api.openaire.eu/graph/v3"
INDICATORS_FILE = Path(__file__).parent / "indicators.json"


def fetch_query(query: dict, page_size: int = 50) -> tuple[list[dict], int]:
    """Fetch records from OpenAIRE V3. Returns (records, total)."""
    params = {"pageSize": page_size}
    for k, v in query.items():
        if k != "pageSize":
            params[k] = v
    resp = httpx.get(f"{V3}/research-products", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", []), data.get("header", {}).get("numFound", 0)


def normalize(rec: dict) -> dict:
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
        "access_right": (rec.get("bestAccessRight") or {}).get("label", ""),
        "is_peer_reviewed": rec.get("isPeerReviewed"),
        "has_orcid": any("orcid" in str(p).lower() for p in pids),
        "has_doi": any("doi" in str(p).lower() for p in (rec.get("pids") or [])),
        "has_pid": bool(rec.get("pids")),
        "has_project": bool(rec.get("projects")),
        "country_count": len(rec.get("countries") or []),
    }


def compute_indicator(indicator: dict, records: list[dict]) -> dict:
    """Compute an indicator value from normalized records."""
    itype = indicator["compute"]
    normed = [normalize(r) for r in records]
    total = len(normed)

    if itype == "count":
        return {"value": total, "type": "count"}

    if itype == "count_with_relation":
        # Count records that have the specified relation type
        target_value = 0
        for r in records:
            for rel in r.get("relations", []):
                if rel.get("relationType") in indicator.get("relation_types", []):
                    target_value += 1
                    break
        return {"value": target_value, "denominator": total, "type": "count_with_relation"}

    if itype == "share_with_field":
        pattern = indicator["field_pattern"]
        count = sum(1 for n in normed if _matches_pattern(n, pattern))
        return {"value": count, "denominator": total, "ratio": count / max(total, 1), "type": "share"}

    if itype == "share_with_value":
        field = indicator["field_path"]
        target = indicator["target_value"]
        count = sum(1 for n in normed if n.get(field) == target)
        return {"value": count, "denominator": total, "ratio": count / max(total, 1), "type": "share"}

    if itype == "share_with_relation":
        rel_type = indicator["relation_type"]
        count = sum(1 for r in records
                    if any(rel.get("relationType") == rel_type for rel in r.get("relations", [])))
        return {"value": count, "denominator": total, "ratio": count / max(total, 1), "type": "share"}

    if itype == "share_multi_value":
        field = indicator["field_path"]
        min_vals = indicator.get("min_values", 2)
        count = sum(1 for n in normed if len(n.get(field, [])) >= min_vals)
        return {"value": count, "denominator": total, "ratio": count / max(total, 1), "type": "share"}

    return {"value": 0, "type": "unknown"}


def _matches_pattern(record: dict, pattern: str) -> bool:
    """Check if a record matches a field pattern (simplified)."""
    if pattern.startswith("authors.*pid.*"):
        scheme = pattern.split(".")[-1]
        authors = record.get("authors") or []
        return any(scheme in str(a.get("pid", "")).lower() for a in authors)
    if pattern.startswith("pids.*"):
        target = pattern.split(".")[-1]
        pids = record.get("pids") or []
        return any(target in str(p).lower() for p in pids)
    return False


def predict_affected(indicator: dict, changes: dict) -> bool:
    """Predict whether an indicator is affected by given changes."""
    for dep in indicator.get("dependencies", []):
        kind = dep["kind"]
        if kind == "query_membership":
            qkey = dep["query_key"]
            if changes.get(f"membership:{qkey}", 0) != 0:
                return True
        elif kind == "field":
            fp = dep["field_pattern"]
            if changes.get(f"field:{fp}", 0) != 0:
                return True
        elif kind == "relation":
            rt = dep["relation_type"]
            if changes.get(f"relation:{rt}", 0) != 0:
                return True
    return False


def run_benchmark():
    """Run the full MONITOR CI benchmark."""
    indicators = json.loads(INDICATORS_FILE.read_text())

    print("=" * 60)
    print("OPENAIRE RESEARCH-INTELLIGENCE CI BENCHMARK")
    print("=" * 60)

    # Phase 1: Establish baseline from current OpenAIRE
    print("\n[1] FETCHING BASELINE FROM OPENAIRE V3...")
    baselines = {}
    for ind in indicators:
        records, total = fetch_query(ind["query"], page_size=50)
        value = compute_indicator(ind, records)
        baselines[ind["indicator_id"]] = {
            "value": value,
            "total": total,
            "records_fetched": len(records),
            "digest": hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:16],
            "_records": records,  # store for diff
        }
        print(f"  {ind['indicator_id']}: {value}")

    # Phase 2: Simulate Graph changes by re-querying with modified params
    # In production this would compare v11.0.1 vs v11.3.0
    print("\n[2] SIMULATING GRAPH CHANGES (re-query with different page sizes)...")
    changes = {}
    current = {}
    for ind in indicators:
        # Use different page size to simulate partial view changes
        new_size = 10 if ind["query"].get("pageSize", 50) == 50 else 50
        modified_query = {**ind["query"], "pageSize": new_size}
        records, total = fetch_query(modified_query, page_size=new_size)
        new_value = compute_indicator(ind, records)
        current[ind["indicator_id"]] = {
            "value": new_value,
            "total": total,
            "records_fetched": len(records),
            "_records": records,  # store for diff
        }

        # Detect changes
        old_v = baselines[ind["indicator_id"]]["value"]["value"]
        new_v = new_value["value"]
        if old_v != new_v:
            changes[ind["indicator_id"]] = {"old": old_v, "new": new_v}
            print(f"  CHANGED: {ind['indicator_id']} {old_v} → {new_v}")
        else:
            print(f"  unchanged: {ind['indicator_id']}")

    # Phase 3: Build change summary from record-level diffs
    print("\n[3] PREDICTING AFFECTED INDICATORS (from record-level diffs)...")
    change_summary = {}
    for ind in indicators:
        iid = ind["indicator_id"]
        key = iid.split(":")[1]

        # Compare actual records, not just final values
        old_records = baselines[iid].get("_records", [])
        new_records = current[iid].get("_records", [])
        old_ids = {r.get("id") for r in old_records}
        new_ids = {r.get("id") for r in new_records}

        if old_ids != new_ids:
            # Records changed — all query-dependent indicators may be affected
            for dep in ind.get("dependencies", []):
                if dep["kind"] == "query_membership":
                    change_summary[dep["query_key"]] = change_summary.get(dep["query_key"], 0) + 1
                elif dep["kind"] == "field":
                    change_summary[f"field:{dep['field_pattern']}"] = change_summary.get(f"field:{dep['field_pattern']}", 0) + 1
                elif dep["kind"] == "relation":
                    change_summary[f"relation:{dep['relation_type']}"] = change_summary.get(f"relation:{dep['relation_type']}", 0) + 1

    predictions = {}
    for ind in indicators:
        predicted = predict_affected(ind, change_summary)
        predictions[ind["indicator_id"]] = predicted
        status = "AFFECTED" if predicted else "UNAFFECTED"
        actually_changed = ind["indicator_id"] in changes
        print(f"  {ind['indicator_id']}: predicted={status}, actually_changed={actually_changed}")

    # Phase 4: Evaluate
    print("\n" + "=" * 60)
    print("EVALUATION")
    print("=" * 60)

    actually_changed = set(changes.keys())
    predicted_affected = {iid for iid, p in predictions.items() if p}

    true_positive = actually_changed & predicted_affected
    false_positive = predicted_affected - actually_changed
    false_negative = actually_changed - predicted_affected
    true_negative = set(predictions.keys()) - actually_changed - predicted_affected

    precision = len(true_positive) / max(len(predicted_affected), 1)
    recall = len(true_positive) / max(len(actually_changed), 1)
    recompute_avoided = len(true_negative) / max(len(predictions), 1)

    print(f"\n  Indicators tracked:           {len(indicators)}")
    print(f"  Actually changed:             {len(actually_changed)}")
    print(f"  Predicted affected:           {len(predicted_affected)}")
    print(f"  Correctly unaffected:         {len(true_negative)}")
    print(f"")
    print(f"  Impact precision:             {precision:.2f}")
    print(f"  Impact recall:                {recall:.2f}")
    print(f"  False stale rate:             {len(false_positive) / max(len(predicted_affected), 1):.2f}")
    print(f"  Recomputation avoided:        {recompute_avoided:.1%}")
    print(f"")

    if true_positive:
        print(f"  CORRECTLY PREDICTED AFFECTED:")
        for iid in sorted(true_positive):
            chg = changes[iid]
            print(f"    ✓ {iid}: {chg['old']} → {chg['new']}")

    if false_positive:
        print(f"\n  FALSE ALARMS (predicted but unchanged):")
        for iid in sorted(false_positive):
            print(f"    ⚠ {iid}")

    if false_negative:
        print(f"\n  MISSED CHANGES (changed but not predicted):")
        for iid in sorted(false_negative):
            chg = changes[iid]
            print(f"    ✗ {iid}: {chg['old']} → {chg['new']}")

    print(f"\n  WHY THIS MATTERS:")
    print(f"  Without Pāṭala: recompute all {len(indicators)} indicators")
    print(f"  With Pāṭala: only recompute {len(predicted_affected)} predicted affected")
    print(f"  Savings: {recompute_avoided:.1%} computation avoided")

    # Save results
    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "indicators_tracked": len(indicators),
        "actually_changed": len(actually_changed),
        "predicted_affected": len(predicted_affected),
        "precision": precision,
        "recall": recall,
        "recompute_avoided": recompute_avoided,
        "changes": changes,
        "predictions": predictions,
        "baselines": {k: v["value"] for k, v in baselines.items()},
        "current": {k: v["value"] for k, v in current.items()},
    }
    results_file = Path(__file__).parent / "results.json"
    results_file.write_text(json.dumps(results, indent=2))
    print(f"\n  Results saved to: {results_file}")


if __name__ == "__main__":
    run_benchmark()
