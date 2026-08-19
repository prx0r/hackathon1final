from __future__ import annotations

from typing import Any

from .model import Snapshot, TrackedClaim


def _get_path(obj: dict[str, Any], path: str) -> Any:
    cur: Any = obj
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _match(item: dict[str, Any], where: dict[str, Any] | None) -> bool:
    if not where:
        return True
    field = where.get("field")
    if not field:
        return True
    value = _get_path(item, field)
    if "equals" in where:
        return value == where["equals"]
    if "in" in where:
        return value in where["in"]
    if "truthy" in where:
        return bool(value) is bool(where["truthy"])
    return True


def _compare(value: float | int, op: str, threshold: float | int) -> bool:
    return {
        ">=": value >= threshold,
        ">": value > threshold,
        "<=": value <= threshold,
        "<": value < threshold,
        "==": value == threshold,
        "!=": value != threshold,
    }.get(op, False)


def evaluate_claim(claim: TrackedClaim, snapshot: Snapshot) -> dict[str, Any]:
    spec = claim.computation
    if not spec:
        return {"computable": False, "value": None, "supported": None, "reason": "manual claim"}
    typ = spec.get("type")
    op = spec.get("op", ">=")
    threshold = spec.get("threshold", 0)

    if typ == "count":
        value = sum(1 for item in snapshot.items if _match(item, spec.get("where")))
        return {"computable": True, "value": value, "supported": _compare(value, op, threshold)}

    if typ == "ratio":
        denom_items = [x for x in snapshot.items if _match(x, spec.get("denominator"))]
        num_items = [x for x in denom_items if _match(x, spec.get("numerator"))]
        value = (len(num_items) / len(denom_items)) if denom_items else 0.0
        return {"computable": True, "value": value, "supported": _compare(value, op, threshold),
                "numerator": len(num_items), "denominator": len(denom_items)}

    if typ == "ratio_relation":
        relation = spec.get("relation")
        target_type = spec.get("target_type")
        entities = {x.get("id") for x in snapshot.items if x.get("id")}
        # A relation can reference the OpenAIRE entity id or its PID in fixture/live adapters.
        pids_by_entity = {}
        for item in snapshot.items:
            ids = {item.get("id")}
            ids |= {p.get("value") for p in item.get("pids", []) if p.get("value")}
            pids_by_entity[item.get("id")] = ids
        hits: set[str] = set()
        for r in snapshot.relations:
            if relation and r.get("relation") != relation:
                continue
            if target_type and str(r.get("target_type") or "").lower() != str(target_type).lower():
                continue
            src = r.get("source")
            for entity_id, ids in pids_by_entity.items():
                if src in ids:
                    hits.add(entity_id)
        value = (len(hits) / len(entities)) if entities else 0.0
        return {"computable": True, "value": value, "supported": _compare(value, op, threshold),
                "numerator": len(hits), "denominator": len(entities)}

    return {"computable": False, "value": None, "supported": None, "reason": f"unknown computation type {typ}"}
