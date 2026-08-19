from __future__ import annotations

import hashlib
import json
from typing import Any

# Transport/runtime fields that must never make a scholarly-state digest unstable.
VOLATILE_KEYS = {
    "queryTime", "requestTime", "responseTime", "elapsed", "timestamp",
    "nextCursor", "cursor", "page", "pageSize", "page_size", "maxScore",
}


def canonicalize(value: Any, *, drop_volatile: bool = False) -> Any:
    """Return a deterministic JSON-compatible structure.

    Dict keys are sorted by JSON serialization. List order is preserved because author
    order and other scholarly sequences may be meaningful. Only explicitly volatile
    transport fields are removed when requested.
    """
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key in sorted(value):
            if drop_volatile and key in VOLATILE_KEYS:
                continue
            out[str(key)] = canonicalize(value[key], drop_volatile=drop_volatile)
        return out
    if isinstance(value, list):
        return [canonicalize(v, drop_volatile=drop_volatile) for v in value]
    if isinstance(value, tuple):
        return [canonicalize(v, drop_volatile=drop_volatile) for v in value]
    return value


def canonical_json_bytes(value: Any, *, drop_volatile: bool = False) -> bytes:
    return json.dumps(
        canonicalize(value, drop_volatile=drop_volatile),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest_json(value: Any, algorithm: str = "sha256", *, drop_volatile: bool = False) -> str:
    data = canonical_json_bytes(value, drop_volatile=drop_volatile)
    h = hashlib.new(algorithm)
    h.update(data)
    return f"{algorithm}:{h.hexdigest()}"


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()
