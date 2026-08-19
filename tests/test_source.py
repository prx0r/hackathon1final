import unittest
from patala_research_ci.source import FunctionTransport
from patala_research_ci.openaire import GraphV3Client
from patala_research_ci.model import QuerySpec

class SourceTests(unittest.TestCase):
    def test_empty_is_not_failure(self):
        t=FunctionTransport(lambda url,params:{'header':{'numFound':0},'results':[]})
        r=GraphV3Client(t).search(QuerySpec())
        self.assertEqual(r.status,'OK'); self.assertEqual(r.items,[])

    def test_failure_is_not_empty(self):
        def bad(url,params): raise RuntimeError('down')
        r=GraphV3Client(FunctionTransport(bad)).search(QuerySpec())
        self.assertEqual(r.status,'UNAVAILABLE'); self.assertEqual(r.items,[]); self.assertIn('down',r.error)
