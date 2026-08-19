import unittest
from patala_research_ci.lineage import LineageGraph, LineageArtifact, LineageEdge, ArtifactKind, ArtifactState

class LineageTests(unittest.TestCase):
    def build(self):
        g=LineageGraph()
        g.add(LineageArtifact("obs:a", ArtifactKind.OBSERVATION.value, {"v":1}))
        g.add(LineageArtifact("obs:b", ArtifactKind.OBSERVATION.value, {"v":2}))
        g.add(LineageArtifact("claim:a", ArtifactKind.CLAIM.value, {"x":1}, dependencies=[LineageEdge("obs:a")]))
        g.add(LineageArtifact("report:a", ArtifactKind.REPORT.value, {"x":2}, dependencies=[LineageEdge("claim:a", trust=.9)]))
        g.add(LineageArtifact("claim:b", ArtifactKind.CLAIM.value, {"x":3}, dependencies=[LineageEdge("obs:b")]))
        return g
    def test_selective_invalidation(self):
        g=self.build(); p=g.mark_invalidated(["obs:a"])
        self.assertEqual(p["affected"], ["claim:a","report:a"])
        self.assertIn("claim:b", p["unaffected"])
        self.assertEqual(g.nodes["claim:a"].state, ArtifactState.REVERIFY_REQUIRED.value)
        self.assertEqual(g.nodes["claim:b"].state, ArtifactState.CURRENT.value)
    def test_execution_key_is_structure_and_input_bound(self):
        g1=self.build(); g2=self.build()
        self.assertEqual(g1.nodes["report:a"].execution_key, g2.nodes["report:a"].execution_key)
        g3=LineageGraph(); g3.add(LineageArtifact("obs:a", "observation", {"v":99})); g3.add(LineageArtifact("claim:a","claim",{"x":1},dependencies=[LineageEdge("obs:a")]))
        self.assertNotEqual(g1.nodes["claim:a"].execution_key, g3.nodes["claim:a"].execution_key)
    def test_cycle_or_missing_dep_rejected(self):
        g=LineageGraph()
        with self.assertRaises(KeyError): g.add(LineageArtifact("x","claim",{},dependencies=[LineageEdge("missing")]))

if __name__=='__main__': unittest.main()
