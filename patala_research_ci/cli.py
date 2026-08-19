from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from .dashboard import serve as serve_dashboard
from .export import export_ro_crate
from .model import Dependency, QuerySpec, Snapshot, TrackedClaim
from .mcp_trace import load_trace, build_trace
from .service import ResearchCI
from .store import Workspace


def _kv(values: list[str] | None) -> dict[str, str]:
    out = {}
    for raw in values or []:
        if "=" not in raw:
            raise SystemExit(f"Expected KEY=VALUE, got: {raw}")
        k, v = raw.split("=", 1)
        out[k] = v
    return out


def _print_json(value: Any):
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    print(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True))


def _load_claims(path: str | None) -> list[TrackedClaim]:
    if not path:
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("claims", [])
    return [TrackedClaim.from_dict(x) for x in data]


def _load_snapshot(path: str) -> Snapshot:
    return Snapshot.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="patala-ci", description="Continuous verification for evolving scholarly knowledge")
    p.add_argument("--workspace", default=".patala-ci", help="Workspace directory")
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("track", help="Track an OpenAIRE query and its claims")
    t.add_argument("--id", required=True); t.add_argument("--title")
    t.add_argument("--entity", default="research-products", choices=["research-products","organizations","datasources","projects","persons"])
    t.add_argument("--search"); t.add_argument("--param", action="append", default=[])
    t.add_argument("--api", default="v3", choices=["v3","v4"])
    t.add_argument("--page-size", type=int, default=25); t.add_argument("--max-pages", type=int, default=1)
    t.add_argument("--relations", action="store_true", help="Enrich research products via ScholeXplorer V3")
    t.add_argument("--relation", help="Optional ScholeXplorer relation semantic")
    t.add_argument("--select", action="append", default=[], help="V4 beta sparse field selection")
    t.add_argument("--facet", action="append", default=[], help="V4 beta facet")
    t.add_argument("--claims", help="JSON file containing TrackedClaim objects")
    t.add_argument("--mcp-trace", help="Alien/OpenAIRE MCP trace JSON to bind to this analysis")

    v = sub.add_parser("verify", help="Re-run a tracked analysis against current OpenAIRE")
    v.add_argument("analysis_id")

    rr = sub.add_parser("resolve", help="Resolve a computable proof obligation with a frozen verification plan")
    rr.add_argument("obligation_id")

    l = sub.add_parser("log", help="Show append-only event history")
    l.add_argument("--tail", type=int, default=50)

    vl = sub.add_parser("verify-ledger", help="Verify hash-chain integrity")

    li = sub.add_parser("list", help="List analyses and proof obligations")

    ex = sub.add_parser("export", help="Export an analysis as an RO-Crate-style ZIP")
    ex.add_argument("analysis_id"); ex.add_argument("--out", required=True)

    d = sub.add_parser("demo", help="Run the complete deterministic offline demo")
    d.add_argument("--fixtures", default=str(Path(__file__).resolve().parents[1] / "fixtures" / "demo"))

    mi = sub.add_parser("mcp-import", help="Import and hash an Alien/OpenAIRE MCP tool-call trace")
    mi.add_argument("trace_file")
    mi.add_argument("--bind", dest="bind_analysis", help="Optional analysis ID to bind the trace to")

    ml = sub.add_parser("mcp-list", help="List imported MCP evidence traces")

    s = sub.add_parser("serve", help="Serve local read-only dashboard")
    s.add_argument("--host", default="127.0.0.1"); s.add_argument("--port", type=int, default=8765)
    return p


def cmd_track(args, ci: ResearchCI):
    spec = QuerySpec(
        entity=args.entity, search=args.search, filters=_kv(args.param), api_version=args.api,
        page_size=args.page_size, max_pages=args.max_pages, include_scholexplorer=args.relations,
        scholexplorer_relation=args.relation, select=args.select, facets=args.facet,
    )
    analysis = ci.track(args.id, args.title or args.id, spec, claims=_load_claims(args.claims))
    trace_info = None
    if args.mcp_trace:
        trace = load_trace(args.mcp_trace)
        ci.ws.save_mcp_trace(trace)
        ci.ws.ledger.append("mcp.trace_imported", trace.trace_id, {
            "trace_digest": trace.digest, "provider": trace.provider, "connector": trace.connector,
            "synthetic": trace.synthetic, "calls": len(trace.calls), "openaire_ids": trace.openaire_ids,
        })
        ci.ws.bind_mcp_trace(analysis.analysis_id, trace.trace_id)
        trace_info = {"trace_id": trace.trace_id, "digest": trace.digest, "synthetic": trace.synthetic}
    snap = ci.ws.load_snapshot(analysis.latest_snapshot_id)
    _print_json({"analysis": analysis.to_dict(), "snapshot": {"id": snap.snapshot_id, "digest": snap.digest,
                 "source_status": snap.source_status, "items": len(snap.items), "relations": len(snap.relations)},
                 "mcp_trace": trace_info})


def cmd_verify(args, ci: ResearchCI):
    r = ci.verify(args.analysis_id)
    _print_json({
        "diff": r["diff"].to_dict(), "impact": r["impact"].to_dict(),
        "obligations": [x.to_dict() for x in r["obligations"]],
        "ledger_state": ci.ws.ledger.state_digest(),
    })


def cmd_demo(args, ci: ResearchCI):
    fixture = Path(args.fixtures)
    baseline = _load_snapshot(str(fixture / "baseline_snapshot.json"))
    current = _load_snapshot(str(fixture / "current_snapshot.json"))
    claims = _load_claims(str(fixture / "claims.json"))
    spec = QuerySpec.from_dict(baseline.query)
    analysis_id = "demo:software-evidence"
    # Clean collision only inside the chosen demo workspace.
    for folder in ("analyses","snapshots","claims","diffs","impacts","obligations","plans","receipts"):
        for p in (ci.ws.root / folder).glob("*.json"):
            p.unlink()
    ci.ws.ledger.path.write_text("", encoding="utf-8")
    ci.track_from_snapshot(analysis_id, "Open research software and linked datasets", spec, baseline, claims,
                           "Deterministic OpenAIRE-shaped fixture demonstrating impact-aware verification.")
    # Exercise the required OpenAIRE-MCP evidence boundary without pretending that
    # an offline test fixture is a live Alien session. This trace is explicitly synthetic.
    trace = build_trace(
        tool_name="search_research_products",
        arguments={"search": "research software", "page_size": 4},
        result={"source": "OpenAIRE MCP fixture", "items": [{"id": x.get("id")} for x in baseline.items]},
        openaire_ids=[str(x.get("id")) for x in baseline.items if x.get("id")],
        client="Pāṭala deterministic demo",
        session_label="offline synthetic MCP-path test",
        synthetic=True,
    )
    ci.ws.save_mcp_trace(trace)
    ci.ws.ledger.append("mcp.trace_imported", trace.trace_id, {
        "trace_digest": trace.digest, "provider": trace.provider, "connector": trace.connector,
        "synthetic": True, "calls": len(trace.calls), "openaire_ids": trace.openaire_ids,
    })
    ci.ws.bind_mcp_trace(analysis_id, trace.trace_id)
    result = ci.verify(analysis_id, supplied_snapshot=current)
    resolved = []
    for ob in result["obligations"]:
        claim = ci.ws.load_claim(ob.claim_id)
        if claim.computation:
            x = ci.resolve_computable(ob.obligation_id)
            resolved.append({"obligation_id": ob.obligation_id, "claim": claim.claim_id,
                             "result": x["evaluation"], "receipt": x["receipt"].receipt_id,
                             "receipt_valid": x["valid"]})
    ok, reason = ci.ws.ledger.verify()
    _print_json({
        "analysis": analysis_id,
        "mcp_trace": {"trace_id": trace.trace_id, "digest": trace.digest, "synthetic": True,
                      "connector": trace.connector, "openaire_ids": trace.openaire_ids},
        "baseline": baseline.digest,
        "current": current.digest,
        "diff_summary": result["diff"].summary,
        "impact": result["impact"].to_dict(),
        "obligations": [x.to_dict() for x in result["obligations"]],
        "auto_resolved": resolved,
        "ledger": {"ok": ok, "reason": reason, "state_digest": ci.ws.ledger.state_digest()},
    })


def cmd_mcp_import(args, ci: ResearchCI):
    trace = load_trace(args.trace_file)
    path = ci.ws.save_mcp_trace(trace)
    ci.ws.ledger.append("mcp.trace_imported", trace.trace_id, {
        "trace_digest": trace.digest,
        "provider": trace.provider,
        "connector": trace.connector,
        "client": trace.client,
        "synthetic": trace.synthetic,
        "calls": len(trace.calls),
        "openaire_ids": trace.openaire_ids,
    })
    binding = None
    if args.bind_analysis:
        binding = ci.ws.bind_mcp_trace(args.bind_analysis, trace.trace_id)
    _print_json({"trace_id": trace.trace_id, "trace_digest": trace.digest, "stored": str(path),
                 "synthetic": trace.synthetic, "openaire_ids": trace.openaire_ids, "binding": binding})


def main(argv: list[str] | None = None):
    args = build_parser().parse_args(argv)
    ws = Workspace(args.workspace)
    ci = ResearchCI(ws)
    if args.cmd == "track": cmd_track(args, ci)
    elif args.cmd == "verify": cmd_verify(args, ci)
    elif args.cmd == "resolve": _print_json(ci.resolve_computable(args.obligation_id))
    elif args.cmd == "log": _print_json(ws.ledger.events()[-args.tail:])
    elif args.cmd == "verify-ledger":
        ok, reason = ws.ledger.verify(); _print_json({"ok": ok, "reason": reason, "state_digest": ws.ledger.state_digest()})
        raise SystemExit(0 if ok else 2)
    elif args.cmd == "list": _print_json({"analyses": ws.list_analyses(), "obligations": ws.list_obligations()})
    elif args.cmd == "export": print(export_ro_crate(ws, args.analysis_id, args.out))
    elif args.cmd == "demo": cmd_demo(args, ci)
    elif args.cmd == "mcp-import": cmd_mcp_import(args, ci)
    elif args.cmd == "mcp-list": _print_json(ws.list_mcp_traces())
    elif args.cmd == "serve": serve_dashboard(args.workspace, args.host, args.port)


if __name__ == "__main__":
    main()
