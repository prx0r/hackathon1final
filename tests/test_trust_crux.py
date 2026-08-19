import unittest
from patala_research_ci.lineage import LineageGraph, LineageArtifact, LineageEdge
from patala_research_ci.trust import PolicyEngine, ActionPolicy
from patala_research_ci.crux import rank_cruxes

class TrustCruxTests(unittest.TestCase):
    def test_gate_and_crux(self):
        g=LineageGraph(); g.add(LineageArtifact('o','observation',{})); g.add(LineageArtifact('c','claim',{},dependencies=[LineageEdge('o',trust=.6)])); g.add(LineageArtifact('r','recommendation',{},dependencies=[LineageEdge('c',trust=.9)]))
        d=PolicyEngine().evaluate(g,'c',ActionPolicy('publish',minimum_path_trust=.7)); self.assertFalse(d.allowed)
        cs=rank_cruxes(g,['r']); self.assertEqual(cs[0].node_id,'o')

if __name__=='__main__': unittest.main()
