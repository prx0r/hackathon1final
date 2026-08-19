import json,unittest
from pathlib import Path
from patala_research_ci.model import Snapshot,TrackedClaim
from patala_research_ci.computation import evaluate_claim
FIX=Path(__file__).resolve().parents[1]/'fixtures'/'demo'

class ComputationTests(unittest.TestCase):
    def test_relation_ratio_can_flip(self):
        old=Snapshot.from_dict(json.loads((FIX/'baseline_snapshot.json').read_text()))
        new=Snapshot.from_dict(json.loads((FIX/'current_snapshot.json').read_text()))
        claims=[TrackedClaim.from_dict(x) for x in json.loads((FIX/'claims.json').read_text())['claims']]
        c=claims[0]
        a=evaluate_claim(c,old);b=evaluate_claim(c,new)
        self.assertTrue(a['supported']);self.assertFalse(b['supported'])
        self.assertAlmostEqual(a['value'],2/3);self.assertAlmostEqual(b['value'],1/4)
