import unittest
from pathlib import Path
from patala_research_ci.mcp_trace import load_trace, build_trace
from patala_research_ci.provenance_guard import candidate_bindings_from_trace, verify_binding

ROOT=Path(__file__).resolve().parents[1]
class ProvenanceGuardTests(unittest.TestCase):
    def test_live_trace_binding(self):
        trace=load_trace(ROOT/'artifacts/alien_mcp_trace.live.json')
        oid='doi_dedup___::25b6bc975c3c7b06cc'
        b=candidate_bindings_from_trace('c',trace,[oid])
        v=verify_binding('c','The selected OpenAIRE record is doi_dedup___::25b6bc975c3c7b06cc.',trace,b)
        self.assertEqual(v.status,'SUPPORTED')
    def test_missing_protected_literal_blocks(self):
        trace=build_trace(tool_name='x',arguments={},result={'id':'doi_________::abcdef123456'},openaire_ids=['doi_________::abcdef123456'])
        b=candidate_bindings_from_trace('c',trace)
        v=verify_binding('c','The rate is 99%.',trace,b)
        self.assertEqual(v.status,'BLOCKED')

if __name__=='__main__': unittest.main()
