from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .model import QuerySpec, SourceStatus
from .normalize import normalize_entity, normalize_scholexplorer_link, primary_pid
from .source import JsonTransport

VALID_ENTITIES = {"research-products", "organizations", "datasources", "projects", "persons"}


@dataclass
class FetchResult:
    status: str
    items: list[dict[str, Any]]
    relations: list[dict[str, Any]]
    header: dict[str, Any]
    request_urls: list[str]
    error: str | None = None


class GraphV3Client:
    base = "https://api.openaire.eu/graph/v3"

    def __init__(self, transport=None):
        self.transport = transport or JsonTransport()

    def search(self, spec: QuerySpec) -> FetchResult:
        if spec.entity not in VALID_ENTITIES:
            return FetchResult(SourceStatus.UNAVAILABLE.value, [], [], {}, [], f"unsupported entity {spec.entity}")
        params = dict(spec.filters)
        if spec.search:
            params["search"] = spec.search
        params["pageSize"] = max(1, min(100, int(spec.page_size)))
        items: list[dict[str, Any]] = []
        urls: list[str] = []
        header: dict[str, Any] = {}
        cursor: str | None = None
        for page_idx in range(max(1, int(spec.max_pages))):
            q = dict(params)
            if spec.max_pages > 1:
                q["cursor"] = "*" if page_idx == 0 else cursor
            else:
                q["page"] = page_idx + 1
            resp = self.transport.get_json(f"{self.base}/{spec.entity}", q)
            urls.append(resp.url)
            if resp.status != SourceStatus.OK.value or not isinstance(resp.body, dict):
                return FetchResult(SourceStatus.UNAVAILABLE.value, [], [], header, urls, resp.error)
            header = resp.body.get("header") or {}
            raw_results = resp.body.get("results") or []
            if not isinstance(raw_results, list):
                return FetchResult(SourceStatus.PARTIAL.value, items, [], header, urls, "results was not a list")
            items.extend(normalize_entity(x, spec.entity) for x in raw_results if isinstance(x, dict))
            cursor = header.get("nextCursor")
            if spec.max_pages <= 1 or not cursor or cursor == q.get("cursor"):
                break
        return FetchResult(SourceStatus.OK.value, items, [], header, urls)

    def get(self, entity: str, openaire_id: str) -> FetchResult:
        if entity not in VALID_ENTITIES:
            return FetchResult(SourceStatus.UNAVAILABLE.value, [], [], {}, [], f"unsupported entity {entity}")
        resp = self.transport.get_json(f"{self.base}/{entity}/{openaire_id}")
        if resp.status != SourceStatus.OK.value or not isinstance(resp.body, dict):
            return FetchResult(SourceStatus.UNAVAILABLE.value, [], [], {}, [resp.url], resp.error)
        return FetchResult(SourceStatus.OK.value, [normalize_entity(resp.body, entity)], [], {}, [resp.url])


class GraphV4Client:
    """Beta adapter. Never required for the core submission path."""
    base = "https://api-beta.openaire.eu/graph/v4"

    def __init__(self, transport=None, mailto: str | None = None):
        self.transport = transport or JsonTransport()
        self.mailto = mailto

    def search(self, spec: QuerySpec) -> FetchResult:
        if spec.entity not in VALID_ENTITIES:
            return FetchResult(SourceStatus.UNAVAILABLE.value, [], [], {}, [], f"unsupported entity {spec.entity}")
        filters = []
        for k, v in spec.filters.items():
            if isinstance(v, (list, tuple)):
                v = "|".join(str(x) for x in v)
            filters.append(f"{k}:{v}")
        params: dict[str, Any] = {"page_size": max(1, min(100, int(spec.page_size)))}
        if spec.search:
            params["search"] = spec.search
        if filters:
            params["filter"] = ",".join(filters)
        if spec.select:
            params["select"] = ",".join(spec.select)
        if spec.facets:
            params["facets"] = ",".join(spec.facets)
        if self.mailto:
            params["mailto"] = self.mailto
        items: list[dict[str, Any]] = []
        urls: list[str] = []
        header: dict[str, Any] = {}
        cursor: str | None = None
        for page_idx in range(max(1, int(spec.max_pages))):
            q = dict(params)
            if spec.max_pages > 1:
                q["cursor"] = "*" if page_idx == 0 else cursor
            else:
                q["page"] = page_idx + 1
            resp = self.transport.get_json(f"{self.base}/{spec.entity}", q)
            urls.append(resp.url)
            if resp.status != SourceStatus.OK.value or not isinstance(resp.body, dict):
                return FetchResult(SourceStatus.UNAVAILABLE.value, [], [], header, urls, resp.error)
            header = resp.body.get("header") or {}
            raw_results = resp.body.get("results") or []
            items.extend(normalize_entity(x, spec.entity) for x in raw_results if isinstance(x, dict))
            cursor = header.get("nextCursor")
            if spec.max_pages <= 1 or not cursor or cursor == q.get("cursor"):
                break
        return FetchResult(SourceStatus.OK.value, items, [], header, urls)


class ScholeXplorerV3Client:
    base = "https://api-beta.scholexplorer.openaire.eu/v3/Links"

    def __init__(self, transport=None):
        self.transport = transport or JsonTransport()

    def links(self, *, source_pid: str | None = None, target_pid: str | None = None,
              relation: str | None = None, page: int = 0) -> FetchResult:
        if not source_pid and not target_pid:
            return FetchResult(SourceStatus.UNAVAILABLE.value, [], [], {}, [], "source_pid or target_pid required")
        params: dict[str, Any] = {"page": page}
        if source_pid:
            params["sourcePid"] = source_pid
        if target_pid:
            params["targetPid"] = target_pid
        if relation:
            params["relation"] = relation
        resp = self.transport.get_json(self.base, params)
        if resp.status != SourceStatus.OK.value or not isinstance(resp.body, dict):
            return FetchResult(SourceStatus.UNAVAILABLE.value, [], [], {}, [resp.url], resp.error)
        raw = resp.body.get("result") or []
        relations = [normalize_scholexplorer_link(x) for x in raw if isinstance(x, dict)]
        return FetchResult(SourceStatus.OK.value, [], relations, {
            "totalLinks": resp.body.get("totalLinks"),
            "totalPages": resp.body.get("totalPages"),
            "currentPage": resp.body.get("currentPage"),
        }, [resp.url])


class BrokerClient:
    base = "https://api.openaire.eu/broker"

    def __init__(self, transport=None):
        self.transport = transport or JsonTransport()

    def subscriptions(self, email: str) -> FetchResult:
        resp = self.transport.get_json(f"{self.base}/subscriptions", {"email": email})
        if resp.status != SourceStatus.OK.value or not isinstance(resp.body, (dict, list)):
            return FetchResult(SourceStatus.UNAVAILABLE.value, [], [], {}, [resp.url], resp.error)
        body = resp.body
        items = body if isinstance(body, list) else body.get("subscriptions") or body.get("results") or []
        return FetchResult(SourceStatus.OK.value, items if isinstance(items, list) else [], [], {}, [resp.url])

    def notifications(self, subscription_id: str, max_pages: int = 1) -> FetchResult:
        urls: list[str] = []
        items: list[dict[str, Any]] = []
        path = f"{self.base}/scroll/notifications/bySubscriptionId/{subscription_id}"
        for _ in range(max(1, max_pages)):
            resp = self.transport.get_json(path)
            urls.append(resp.url)
            if resp.status != SourceStatus.OK.value or not isinstance(resp.body, dict):
                return FetchResult(SourceStatus.UNAVAILABLE.value, items, [], {}, urls, resp.error)
            batch = resp.body.get("notifications") or resp.body.get("results") or resp.body.get("items") or []
            if isinstance(batch, list):
                items.extend(x for x in batch if isinstance(x, dict))
            scroll = resp.body.get("scrollId") or resp.body.get("scroll_id")
            if not scroll:
                break
            path = f"{self.base}/scroll/notifications/{scroll}"
        return FetchResult(SourceStatus.OK.value, items, [], {}, urls)


class OpenAIREStack:
    """Compose Graph + ScholeXplorer. Broker is an independent trigger source."""

    def __init__(self, transport=None, mailto: str | None = None):
        self.transport = transport or JsonTransport()
        self.v3 = GraphV3Client(self.transport)
        self.v4 = GraphV4Client(self.transport, mailto=mailto)
        self.scholexplorer = ScholeXplorerV3Client(self.transport)
        self.broker = BrokerClient(self.transport)

    def fetch(self, spec: QuerySpec) -> FetchResult:
        base = self.v4.search(spec) if spec.api_version.lower() == "v4" else self.v3.search(spec)
        if base.status != SourceStatus.OK.value or not spec.include_scholexplorer:
            return base
        relations: dict[tuple[Any, ...], dict[str, Any]] = {}
        relation_errors = []
        # Bound enrichment to fetched entities; this is intentionally conservative for rate limits.
        for entity in base.items:
            pid = primary_pid(entity)
            if not pid:
                continue
            res = self.scholexplorer.links(source_pid=pid, relation=spec.scholexplorer_relation)
            if res.status != SourceStatus.OK.value:
                relation_errors.append(res.error or "ScholeXplorer unavailable")
                continue
            for r in res.relations:
                key = (r.get("source"), r.get("relation"), r.get("target"), r.get("subtype"))
                relations[key] = r
        status = SourceStatus.PARTIAL.value if relation_errors else SourceStatus.OK.value
        return FetchResult(status, base.items, [relations[k] for k in sorted(relations, key=str)], base.header,
                           base.request_urls, "; ".join(relation_errors) if relation_errors else None)
