from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from .canonical import digest_json
from .model import QuerySpec, Snapshot
from .openaire import OpenAIREStack, FetchResult


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _snapshot_payload(provider: str, api_version: str, query: dict[str, Any], source_status: str,
                      items: list[dict[str, Any]], relations: list[dict[str, Any]]) -> dict[str, Any]:
    # Query result semantics: item/relationship ordering is not meaningful.
    items_sorted = sorted(items, key=lambda x: x.get("id") or "")
    rels_sorted = sorted(relations, key=lambda x: (
        x.get("source") or "", x.get("relation") or "", x.get("target") or "", x.get("subtype") or ""
    ))
    return {
        "provider": provider,
        "api_version": api_version,
        "query": query,
        "source_status": source_status,
        "items": items_sorted,
        "relations": rels_sorted,
    }


def snapshot_from_fetch(spec: QuerySpec, fetched: FetchResult, *, observed_at: str | None = None) -> Snapshot:
    observed_at = observed_at or utc_now()
    payload = _snapshot_payload("openaire", spec.api_version, spec.to_dict(), fetched.status, fetched.items, fetched.relations)
    digest = digest_json(payload)
    return Snapshot(
        snapshot_id=f"snapshot:{uuid.uuid4().hex[:16]}",
        provider="openaire",
        api_version=spec.api_version,
        observed_at=observed_at,
        query=spec.to_dict(),
        source_status=fetched.status,
        source_error=fetched.error,
        items=sorted(fetched.items, key=lambda x: x.get("id") or ""),
        relations=sorted(fetched.relations, key=lambda x: (
            x.get("source") or "", x.get("relation") or "", x.get("target") or "", x.get("subtype") or ""
        )),
        header=fetched.header,
        digest=digest,
    )


def fetch_snapshot(stack: OpenAIREStack, spec: QuerySpec) -> Snapshot:
    return snapshot_from_fetch(spec, stack.fetch(spec))
