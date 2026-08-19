from __future__ import annotations

"""Hardened MCP Streamable-HTTP client/gateway for Alien OpenAIRE.

Supports the MCP 2026-07-28 stateless HTTP shape and a conservative fallback to
legacy Streamable HTTP initialization. Calls can be captured as Pāṭala MCPTrace
objects without exposing Authorization/cookie material.
"""

from dataclasses import dataclass, field
from typing import Any
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
import uuid

from .canonical import digest_json
from .mcp_trace import MCPToolCall, MCPTrace, extract_openaire_ids, _sanitize
from .ledger import utc_now

MODERN_PROTOCOL = "2026-07-28"
LEGACY_PROTOCOL = "2025-06-18"
ALIEN_OPENAIRE_MCP = "https://openaire.mcp.alien.club/mcp"


class MCPTransportError(RuntimeError):
    pass


@dataclass(frozen=True)
class TrustedMCPServer:
    url: str = ALIEN_OPENAIRE_MCP
    server_id: str = "alien:openaire"
    allowed_tools: tuple[str, ...] = ()  # empty = discovery-only allow all
    pinned_tool_schema_digests: dict[str, str] = field(default_factory=dict)
    require_https: bool = True

    def validate_url(self):
        u = urllib.parse.urlparse(self.url)
        if self.require_https and u.scheme != "https":
            raise ValueError("remote MCP server must use https")
        if not u.hostname:
            raise ValueError("invalid MCP server URL")


@dataclass
class MCPResponse:
    result: dict[str, Any]
    headers: dict[str, str]
    protocol: str


class StreamableHTTPClient:
    def __init__(self, server: TrustedMCPServer, timeout: float = 45.0, client_name: str = "patala-continuity", client_version: str = "0.3.0"):
        server.validate_url()
        self.server = server
        self.timeout = timeout
        self.client_name = client_name
        self.client_version = client_version
        self._legacy_session_id: str | None = None
        self._legacy_initialized = False
        self._id = 0
        self._tool_cache: dict[str, dict[str, Any]] = {}

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    def _meta(self, protocol: str) -> dict[str, Any]:
        return {
            "io.modelcontextprotocol/protocolVersion": protocol,
            "io.modelcontextprotocol/clientInfo": {"name": self.client_name, "version": self.client_version},
            "io.modelcontextprotocol/clientCapabilities": {},
        }

    @staticmethod
    def _parse_body(content_type: str, raw: bytes, request_id: int | None) -> dict[str, Any]:
        text = raw.decode("utf-8", errors="replace")
        if "text/event-stream" not in content_type.lower():
            return json.loads(text) if text.strip() else {}
        final: dict[str, Any] | None = None
        for line in text.splitlines():
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if not payload or payload == "[DONE]":
                continue
            try:
                obj = json.loads(payload)
            except json.JSONDecodeError:
                continue
            if request_id is None or obj.get("id") == request_id:
                final = obj
        if final is None:
            raise MCPTransportError("SSE response ended without JSON-RPC result")
        return final

    def _post(self, method: str, params: dict[str, Any] | None, protocol: str, *, name_header: str | None = None, notification: bool = False) -> MCPResponse:
        rid = None if notification else self._next_id()
        body: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if rid is not None:
            body["id"] = rid
        if params is not None:
            params = dict(params)
            if protocol == MODERN_PROTOCOL:
                params.setdefault("_meta", self._meta(protocol))
            body["params"] = params
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": protocol,
            "User-Agent": f"{self.client_name}/{self.client_version}",
        }
        if protocol == MODERN_PROTOCOL:
            headers["Mcp-Method"] = method
            if name_header:
                headers["Mcp-Name"] = name_header.encode("ascii", "ignore").decode()[:200]
        if self._legacy_session_id:
            headers["Mcp-Session-Id"] = self._legacy_session_id
        req = urllib.request.Request(self.server.url, data=json.dumps(body).encode(), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=ssl.create_default_context()) as resp:
                raw = resp.read()
                out_headers = {k: v for k, v in resp.headers.items()}
                session = resp.headers.get("Mcp-Session-Id")
                if session:
                    self._legacy_session_id = session
                parsed = self._parse_body(resp.headers.get("Content-Type", ""), raw, rid)
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            msg = raw.decode("utf-8", errors="replace")
            raise MCPTransportError(f"HTTP {exc.code}: {msg[:1000]}") from exc
        except urllib.error.URLError as exc:
            raise MCPTransportError(str(exc)) from exc
        if notification:
            return MCPResponse({}, out_headers, protocol)
        if "error" in parsed:
            raise MCPTransportError(f"MCP error: {parsed['error']}")
        return MCPResponse(parsed.get("result") or {}, out_headers, protocol)

    def _legacy_initialize(self) -> None:
        if self._legacy_initialized:
            return
        rid = self._next_id()
        body = {
            "jsonrpc": "2.0", "id": rid, "method": "initialize",
            "params": {
                "protocolVersion": LEGACY_PROTOCOL,
                "capabilities": {},
                "clientInfo": {"name": self.client_name, "version": self.client_version},
            },
        }
        req = urllib.request.Request(self.server.url, data=json.dumps(body).encode(), headers={
            "Content-Type": "application/json", "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": LEGACY_PROTOCOL,
        }, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=ssl.create_default_context()) as resp:
                parsed = self._parse_body(resp.headers.get("Content-Type", ""), resp.read(), rid)
                self._legacy_session_id = resp.headers.get("Mcp-Session-Id")
        except Exception as exc:
            raise MCPTransportError(f"legacy initialize failed: {exc}") from exc
        if "error" in parsed:
            raise MCPTransportError(f"legacy initialize error: {parsed['error']}")
        # Legacy clients announce initialization. Some servers accept 202 with no body.
        try:
            self._post("notifications/initialized", {}, LEGACY_PROTOCOL, notification=True)
        except MCPTransportError:
            pass
        self._legacy_initialized = True

    def request(self, method: str, params: dict[str, Any] | None = None, *, name_header: str | None = None) -> MCPResponse:
        try:
            return self._post(method, params, MODERN_PROTOCOL, name_header=name_header)
        except MCPTransportError as modern_error:
            # A compatibility fallback is valuable for servers that have not yet moved to
            # the July-2026 stateless MCP era. We never silently change server URL.
            try:
                self._legacy_initialize()
                return self._post(method, params, LEGACY_PROTOCOL, name_header=name_header)
            except MCPTransportError:
                raise modern_error

    def list_tools(self) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        cursor = None
        for _ in range(50):
            params = {} if cursor is None else {"cursor": cursor}
            result = self.request("tools/list", params).result
            batch = result.get("tools") or []
            for tool in batch:
                if not isinstance(tool, dict) or not tool.get("name"):
                    continue
                name = str(tool["name"])
                schema_digest = digest_json(tool.get("inputSchema") or {})
                expected = self.server.pinned_tool_schema_digests.get(name)
                if expected and schema_digest != expected:
                    continue
                if self.server.allowed_tools and name not in self.server.allowed_tools:
                    continue
                tool = dict(tool); tool["_patala_schema_digest"] = schema_digest
                tools.append(tool); self._tool_cache[name] = tool
            cursor = result.get("nextCursor")
            if not cursor:
                break
        return tools

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if self.server.allowed_tools and name not in self.server.allowed_tools:
            raise PermissionError(f"tool not allowlisted: {name}")
        if name not in self._tool_cache:
            self.list_tools()
        tool = self._tool_cache.get(name)
        if not tool:
            raise KeyError(f"tool not available or schema pin rejected: {name}")
        return self.request("tools/call", {"name": name, "arguments": arguments}, name_header=name).result


class ProvenanceGateway:
    """Wrap MCP calls and produce source-preserving, credential-redacted traces."""

    def __init__(self, client: StreamableHTTPClient, session_label: str | None = None):
        self.client = client
        self.trace_id = "mcp:" + uuid.uuid4().hex[:16]
        self.session_label = session_label
        self.calls: list[MCPToolCall] = []

    def list_tools(self) -> list[dict[str, Any]]:
        return self.client.list_tools()

    def call(self, tool_name: str, arguments: dict[str, Any], notes: str = "") -> dict[str, Any]:
        result = self.client.call_tool(tool_name, arguments)
        clean_args = _sanitize(arguments)
        clean_result = _sanitize(result)
        ids = tuple(extract_openaire_ids(clean_result))
        self.calls.append(MCPToolCall(tool_name, clean_args, clean_result, called_at=utc_now(), openaire_ids=ids, notes=notes))
        return result

    def trace(self) -> MCPTrace:
        if not self.calls:
            raise ValueError("gateway trace has no calls")
        return MCPTrace(
            trace_id=self.trace_id,
            provider="Alien Intelligence",
            connector="OpenAIRE MCP",
            calls=tuple(self.calls),
            captured_at=utc_now(),
            client=self.client.client_name,
            session_label=self.session_label,
            synthetic=False,
        )
