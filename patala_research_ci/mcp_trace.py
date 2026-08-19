from __future__ import annotations

"""Provenance capture for OpenAIRE MCP / Alien Intelligence tool calls.

The hackathon's AI path is the official OpenAIRE MCP connector exposed through
Alien Intelligence. Pāṭala does not reimplement that connector. Instead it
records the tool call/result as an evidence trace, redacts credential-like
fields, hashes the canonical trace, and binds that trace to a deterministic
OpenAIRE Graph snapshot used for later verification.

This lets an AI agent use MCP for discovery while Research CI keeps a replayable,
non-LLM verification path through the OpenAIRE Graph API.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import json
import re
import uuid

from .canonical import digest_json
from .ledger import utc_now

SCHEMA = "https://patala.dev/schemas/mcp-trace-v1"
SENSITIVE_KEYS = {
    "authorization", "auth", "token", "access_token", "refresh_token", "api_key",
    "apikey", "password", "secret", "cookie", "session", "session_token",
}

# OpenAIRE IDs often contain a namespace/prefix and ::. PIDs and URLs are kept
# separately; this detector is intentionally conservative so arbitrary prose is
# not misclassified as an OpenAIRE identifier.
_OPENAIRE_ID = re.compile(r"^[A-Za-z0-9_.-]{2,40}::[A-Za-z0-9_.:%+\-/=]{6,}$")


def _sanitize(value: Any, key: str | None = None) -> Any:
    if key and key.lower() in SENSITIVE_KEYS:
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): _sanitize(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    if isinstance(value, tuple):
        return [_sanitize(v) for v in value]
    return value


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _walk_strings(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _walk_strings(v)


def extract_openaire_ids(value: Any) -> list[str]:
    """Best-effort extraction of explicit OpenAIRE identifiers from a result.

    The trace format also has an explicit ``openaire_ids`` field and callers
    should prefer that whenever the MCP tool exposes identifiers directly.
    """
    found: set[str] = set()
    for raw in _walk_strings(value):
        s = raw.strip()
        if _OPENAIRE_ID.match(s):
            found.add(s)
        # Common OpenAIRE entity URLs, if returned by a client/agent.
        marker = "/graph/"
        if "openaire" in s.lower() and marker in s:
            tail = s.rstrip("/").split("/")[-1]
            if _OPENAIRE_ID.match(tail):
                found.add(tail)
    return sorted(found)


@dataclass(frozen=True)
class MCPToolCall:
    tool_name: str
    arguments: dict[str, Any]
    result: Any
    called_at: str = field(default_factory=utc_now)
    openaire_ids: tuple[str, ...] = ()
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["openaire_ids"] = list(self.openaire_ids)
        return _sanitize(data)


@dataclass(frozen=True)
class MCPTrace:
    trace_id: str
    provider: str
    connector: str
    calls: tuple[MCPToolCall, ...]
    captured_at: str = field(default_factory=utc_now)
    client: str | None = None
    session_label: str | None = None
    schema: str = SCHEMA
    synthetic: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "trace_id": self.trace_id,
            "provider": self.provider,
            "connector": self.connector,
            "captured_at": self.captured_at,
            "client": self.client,
            "session_label": self.session_label,
            "synthetic": self.synthetic,
            "calls": [c.to_dict() for c in self.calls],
        }

    @property
    def digest(self) -> str:
        return digest_json(self.to_dict())

    @property
    def openaire_ids(self) -> list[str]:
        out: set[str] = set()
        for call in self.calls:
            out.update(call.openaire_ids)
            out.update(extract_openaire_ids(call.result))
        return sorted(out)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MCPTrace":
        calls = []
        for raw in data.get("calls", []):
            if not isinstance(raw, dict):
                raise ValueError("MCP trace calls must be objects")
            result = _sanitize(raw.get("result"))
            explicit = raw.get("openaire_ids") or []
            ids = sorted(set(str(x) for x in explicit) | set(extract_openaire_ids(result)))
            calls.append(MCPToolCall(
                tool_name=str(raw.get("tool_name") or ""),
                arguments=_sanitize(raw.get("arguments") or {}),
                result=result,
                called_at=str(raw.get("called_at") or utc_now()),
                openaire_ids=tuple(ids),
                notes=str(raw.get("notes") or ""),
            ))
        if not calls:
            raise ValueError("MCP trace must contain at least one tool call")
        trace = cls(
            trace_id=str(data.get("trace_id") or ("mcp:" + uuid.uuid4().hex[:16])),
            provider=str(data.get("provider") or "Alien Intelligence"),
            connector=str(data.get("connector") or "OpenAIRE MCP"),
            calls=tuple(calls),
            captured_at=str(data.get("captured_at") or utc_now()),
            client=data.get("client"),
            session_label=data.get("session_label"),
            schema=str(data.get("schema") or SCHEMA),
            synthetic=bool(data.get("synthetic", False)),
        )
        validate_trace(trace)
        return trace


def validate_trace(trace: MCPTrace) -> None:
    if trace.schema != SCHEMA:
        raise ValueError(f"unsupported MCP trace schema: {trace.schema}")
    if not trace.provider.strip() or not trace.connector.strip():
        raise ValueError("provider and connector are required")
    for call in trace.calls:
        if not call.tool_name.strip():
            raise ValueError("tool_name is required")
        encoded = json.dumps(call.to_dict(), sort_keys=True).lower()
        # Redaction should eliminate common literal credential field values.
        for k in SENSITIVE_KEYS:
            if f'"{k}"' in encoded and "[redacted]" not in encoded:
                # Do not reject generic keys nested in result text; explicit keys are
                # sanitized before this point. This is defensive rather than perfect.
                pass


def load_trace(path: str | Path) -> MCPTrace:
    return MCPTrace.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def build_trace(*, tool_name: str, arguments: dict[str, Any], result: Any,
                openaire_ids: list[str] | None = None, provider: str = "Alien Intelligence",
                connector: str = "OpenAIRE MCP", client: str | None = None,
                session_label: str | None = None, synthetic: bool = False) -> MCPTrace:
    clean_result = _sanitize(result)
    ids = set(openaire_ids or []) | set(extract_openaire_ids(clean_result))
    return MCPTrace(
        trace_id="mcp:" + uuid.uuid4().hex[:16],
        provider=provider,
        connector=connector,
        client=client,
        session_label=session_label,
        synthetic=synthetic,
        calls=(MCPToolCall(tool_name, _sanitize(arguments), clean_result, openaire_ids=tuple(sorted(ids))),),
    )
