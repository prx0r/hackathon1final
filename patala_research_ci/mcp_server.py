"""MCP surface for AI-agent workflows.

This server is intentionally complementary to the official OpenAIRE MCP powered
by Alien Intelligence:

1. the agent queries OpenAIRE through the official MCP;
2. the agent records the exact tool call/result with ``record_openaire_mcp_call``;
3. Pāṭala binds that evidence trace to a deterministic Graph API snapshot;
4. later, the agent calls ``verify_analysis`` to discover proof obligations.

Install with: pip install -e '.[mcp]'
Run with:     PATALA_WORKSPACE=.patala-ci python -m patala_research_ci.mcp_server
"""
from __future__ import annotations

import json
import os


def main():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise SystemExit("MCP extra not installed. Run: pip install -e '.[mcp]'") from exc

    from .mcp_trace import build_trace
    from .service import ResearchCI
    from .store import Workspace

    workspace = os.environ.get("PATALA_WORKSPACE", ".patala-ci")
    ci = ResearchCI(Workspace(workspace))
    mcp = FastMCP("Patala Research CI")

    @mcp.tool()
    def record_openaire_mcp_call(
        tool_name: str,
        arguments_json: str,
        result_json: str,
        openaire_ids_json: str = "[]",
        client: str = "AI client",
        session_label: str = "",
    ) -> dict:
        """Record a call already made through the official OpenAIRE/Alien MCP.

        Credential-like keys are redacted before persistence. This tool never
        requires or stores an Alien token.
        """
        arguments = json.loads(arguments_json or "{}")
        result = json.loads(result_json or "null")
        openaire_ids = json.loads(openaire_ids_json or "[]")
        if not isinstance(openaire_ids, list):
            raise ValueError("openaire_ids_json must decode to a list")
        trace = build_trace(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            openaire_ids=[str(x) for x in openaire_ids],
            client=client,
            session_label=session_label or None,
            synthetic=False,
        )
        path = ci.ws.save_mcp_trace(trace)
        ci.ws.ledger.append("mcp.trace_imported", trace.trace_id, {
            "trace_digest": trace.digest,
            "provider": trace.provider,
            "connector": trace.connector,
            "calls": len(trace.calls),
            "openaire_ids": trace.openaire_ids,
            "synthetic": False,
        })
        return {
            "trace_id": trace.trace_id,
            "trace_digest": trace.digest,
            "stored": str(path),
            "openaire_ids": trace.openaire_ids,
        }

    @mcp.tool()
    def bind_mcp_trace(analysis_id: str, trace_id: str) -> dict:
        """Bind an OpenAIRE MCP evidence trace to a tracked analysis."""
        return ci.ws.bind_mcp_trace(analysis_id, trace_id)

    @mcp.tool()
    def list_mcp_traces() -> list[dict]:
        """List credential-redacted OpenAIRE MCP evidence traces."""
        return ci.ws.list_mcp_traces()

    @mcp.tool()
    def list_tracked_analyses() -> list[dict]:
        """List persistent research analyses tracked against OpenAIRE."""
        return ci.ws.list_analyses()

    @mcp.tool()
    def verify_analysis(analysis_id: str) -> dict:
        """Recheck an analysis against current OpenAIRE state and return semantic impact."""
        r = ci.verify(analysis_id)
        return {
            "diff": r["diff"].to_dict(),
            "impact": r["impact"].to_dict(),
            "obligations": [x.to_dict() for x in r["obligations"]],
        }

    @mcp.tool()
    def list_proof_obligations() -> list[dict]:
        """List explicit unresolved re-verification tasks."""
        return ci.ws.list_obligations()

    @mcp.tool()
    def verify_ledger() -> dict:
        """Verify the append-only evidence ledger."""
        ok, reason = ci.ws.ledger.verify()
        return {"ok": ok, "reason": reason, "state_digest": ci.ws.ledger.state_digest()}

    mcp.run()


if __name__ == "__main__":
    main()
