import json
import tempfile
import unittest
from pathlib import Path

from patala_research_ci.mcp_trace import MCPTrace, build_trace, load_trace
from patala_research_ci.store import Workspace


class MCPTraceTests(unittest.TestCase):
    def test_sensitive_fields_are_redacted_and_trace_hashes(self):
        trace = build_trace(
            tool_name="search_research_products",
            arguments={"query": "research software", "token": "secret"},
            result={"results": [{"id": "doi_dedup___::abcdef123456"}]},
            client="Alien/Claude",
        )
        data = trace.to_dict()
        self.assertEqual(data["calls"][0]["arguments"]["token"], "[REDACTED]")
        self.assertTrue(trace.digest.startswith("sha256:"))
        self.assertIn("doi_dedup___::abcdef123456", trace.openaire_ids)

    def test_synthetic_marker_is_preserved(self):
        trace = build_trace(tool_name="demo", arguments={}, result={}, synthetic=True)
        self.assertTrue(trace.synthetic)
        self.assertTrue(trace.to_dict()["synthetic"])

    def test_workspace_can_bind_trace_to_analysis_event(self):
        from patala_research_ci.model import QuerySpec, Snapshot
        from patala_research_ci.service import ResearchCI
        with tempfile.TemporaryDirectory() as td:
            ws = Workspace(td)
            ci = ResearchCI(ws)
            snap = Snapshot("s","openaire","v3","now",QuerySpec().to_dict(),"OK",None,[],[],{},"sha256:s")
            ci.track_from_snapshot("a","A",QuerySpec(),snap,[])
            trace = build_trace(tool_name="search_research_products", arguments={"search":"x"}, result={"results":[]}, synthetic=True)
            ws.save_mcp_trace(trace)
            ws.bind_mcp_trace("a", trace.trace_id)
            events = ws.ledger.events()
            self.assertEqual(events[-1]["event_type"], "analysis.mcp_bound")
            self.assertEqual(events[-1]["payload"]["trace_digest"], trace.digest)

    def test_load_trace_rejects_empty_calls(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/"x.json"
            p.write_text(json.dumps({"schema":"https://patala.dev/schemas/mcp-trace-v1","provider":"Alien Intelligence","connector":"OpenAIRE MCP","calls":[]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_trace(p)


if __name__ == "__main__":
    unittest.main()
