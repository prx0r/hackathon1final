from __future__ import annotations

from collections import Counter
from typing import Any
import uuid

from .canonical import digest_json
from .model import Change, Materiality, SemanticDiff, Snapshot, SourceStatus


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(value, dict):
        for key in sorted(value):
            path = f"{prefix}.{key}" if prefix else key
            out.update(_flatten(value[key], path))
    elif isinstance(value, list):
        # We compare complete lists at a path. This preserves author order and avoids noisy item indexes.
        out[prefix] = value
    else:
        out[prefix] = value
    return out


def classify_materiality(path: str, before: Any, after: Any) -> str:
    p = path.lower()
    if "is_retracted" in p and bool(after):
        return Materiality.RETRACTION.value
    if "is_corrected" in p and bool(after):
        return Materiality.CORRECTION.value
    if any(x in p for x in ("pids", "orcid", "id")):
        return Materiality.IDENTITY.value
    if any(x in p for x in ("access_right", "license", "availability")):
        return Materiality.AVAILABILITY.value
    if any(x in p for x in ("title", "publisher", "language", "publication_date", "authors", "grants", "is_peer_reviewed")):
        return Materiality.METADATA.value
    if p.endswith("raw_digest"):
        return Materiality.COSMETIC.value
    return Materiality.METADATA.value


def _relation_key(r: dict[str, Any]) -> tuple[str, str, str, str]:
    return (str(r.get("source") or ""), str(r.get("relation") or ""), str(r.get("target") or ""), str(r.get("subtype") or ""))


def diff_snapshots(analysis_id: str, old: Snapshot, new: Snapshot) -> SemanticDiff:
    changes: list[Change] = []

    # Critical invariant: failed/partial upstream retrieval is not a graph deletion event.
    if new.source_status == SourceStatus.UNAVAILABLE.value:
        changes.append(Change(
            change_id="chg:" + uuid.uuid4().hex[:14],
            kind="SOURCE_UNAVAILABLE",
            materiality=Materiality.SOURCE_HEALTH.value,
            reason=new.source_error or "OpenAIRE source unavailable",
        ))
        return SemanticDiff(
            diff_id="diff:" + uuid.uuid4().hex[:14], analysis_id=analysis_id,
            old_snapshot_id=old.snapshot_id, new_snapshot_id=new.snapshot_id,
            old_digest=old.digest, new_digest=new.digest, source_status=new.source_status,
            changes=changes, summary={"SOURCE_UNAVAILABLE": 1},
        )

    # PARTIAL means the primary Graph result is usable but one enrichment plane
    # (for example ScholeXplorer) failed. Entity changes remain comparable, but
    # relation deletions must be suppressed because the relation set is incomplete.
    relations_complete = new.source_status != SourceStatus.PARTIAL.value
    if not relations_complete:
        changes.append(Change(
            change_id="chg:" + uuid.uuid4().hex[:14],
            kind="SOURCE_PARTIAL",
            materiality=Materiality.SOURCE_HEALTH.value,
            reason=new.source_error or "OpenAIRE enrichment partially unavailable; relation deletions suppressed",
        ))

    old_items = {x.get("id"): x for x in old.items if x.get("id")}
    new_items = {x.get("id"): x for x in new.items if x.get("id")}

    for entity_id in sorted(set(new_items) - set(old_items)):
        changes.append(Change(
            change_id="chg:" + uuid.uuid4().hex[:14], kind="ENTITY_ADDED",
            materiality=Materiality.QUERY_MEMBERSHIP.value, entity_id=entity_id,
            after=new_items[entity_id], reason="entity entered tracked query result",
        ))
    for entity_id in sorted(set(old_items) - set(new_items)):
        changes.append(Change(
            change_id="chg:" + uuid.uuid4().hex[:14], kind="ENTITY_REMOVED",
            materiality=Materiality.QUERY_MEMBERSHIP.value, entity_id=entity_id,
            before=old_items[entity_id], reason="entity left tracked query result",
        ))

    for entity_id in sorted(set(old_items) & set(new_items)):
        before = _flatten(old_items[entity_id])
        after = _flatten(new_items[entity_id])
        for path in sorted(set(before) | set(after)):
            if before.get(path) == after.get(path):
                continue
            # raw_digest is a useful fallback signal only if no semantic field changed.
            if path == "raw_digest":
                continue
            changes.append(Change(
                change_id="chg:" + uuid.uuid4().hex[:14], kind="FIELD_CHANGED",
                materiality=classify_materiality(path, before.get(path), after.get(path)),
                entity_id=entity_id, path=path, before=before.get(path), after=after.get(path),
                reason=f"{path} changed",
            ))
        if old_items[entity_id].get("raw_digest") != new_items[entity_id].get("raw_digest"):
            semantic_changed = any(c.entity_id == entity_id and c.kind == "FIELD_CHANGED" for c in changes)
            if not semantic_changed:
                changes.append(Change(
                    change_id="chg:" + uuid.uuid4().hex[:14], kind="RAW_RECORD_CHANGED",
                    materiality=Materiality.COSMETIC.value, entity_id=entity_id, path="raw_digest",
                    before=old_items[entity_id].get("raw_digest"), after=new_items[entity_id].get("raw_digest"),
                    reason="upstream record changed outside normalized semantic fields",
                ))

    old_rel = {_relation_key(r): r for r in old.relations}
    new_rel = {_relation_key(r): r for r in new.relations}

    # Observed additions are positive evidence — always emit them.
    for key in sorted(set(new_rel) - set(old_rel)):
        changes.append(Change(
            change_id="chg:" + uuid.uuid4().hex[:14], kind="RELATION_ADDED",
            materiality=Materiality.RELATION.value, relation=new_rel[key],
            reason="typed scholarly relation added",
        ))

    # Absence is only meaningful with complete retrieval.
    # Under PARTIAL coverage, suppress relation deletions to avoid false alarms.
    if relations_complete:
        for key in sorted(set(old_rel) - set(new_rel)):
            changes.append(Change(
                change_id="chg:" + uuid.uuid4().hex[:14], kind="RELATION_REMOVED",
                materiality=Materiality.RELATION.value, relation=old_rel[key],
                reason="typed scholarly relation removed",
            ))

    summary = dict(Counter(c.kind for c in changes))
    return SemanticDiff(
        diff_id="diff:" + uuid.uuid4().hex[:14], analysis_id=analysis_id,
        old_snapshot_id=old.snapshot_id, new_snapshot_id=new.snapshot_id,
        old_digest=old.digest, new_digest=new.digest, source_status=new.source_status,
        changes=changes, summary=summary,
    )
