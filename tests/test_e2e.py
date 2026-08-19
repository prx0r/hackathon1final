import json,tempfile,unittest
from pathlib import Path
from patala_research_ci.model import QuerySpec,Snapshot,TrackedClaim
from patala_research_ci.service import ResearchCI
from patala_research_ci.store import Workspace
FIX=Path(__file__).resolve().parents[1]/'fixtures'/'demo'

class E2ETests(unittest.TestCase):
    def test_track_verify_oblige_resolve(self):
        with tempfile.TemporaryDirectory() as td:
            ws=Workspace(td);ci=ResearchCI(ws)
            old=Snapshot.from_dict(json.loads((FIX/'baseline_snapshot.json').read_text()))
            new=Snapshot.from_dict(json.loads((FIX/'current_snapshot.json').read_text()))
            claims=[TrackedClaim.from_dict(x) for x in json.loads((FIX/'claims.json').read_text())['claims']]
            ci.track_from_snapshot('a','A',QuerySpec.from_dict(old.query),old,claims)
            r=ci.verify('a',supplied_snapshot=new)
            self.assertGreaterEqual(len(r['obligations']),3)
            comp=[o for o in r['obligations'] if ws.load_claim(o.claim_id).computation]
            results=[ci.resolve_computable(o.obligation_id) for o in comp]
            self.assertTrue(all(x['valid'] for x in results))
            states={x['claim'].claim_id:x['claim'].state for x in results}
            self.assertEqual(states['claim:dataset-linkage'],'UNSUPPORTED')
            self.assertEqual(states['claim:open-access'],'VERIFIED_CURRENT')
            self.assertTrue(ws.ledger.verify()[0])

    def test_failed_verification_does_not_advance_last_good_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            ws=Workspace(td);ci=ResearchCI(ws)
            old=Snapshot.from_dict(json.loads((FIX/'baseline_snapshot.json').read_text()))
            ci.track_from_snapshot('a','A',QuerySpec.from_dict(old.query),old,[])
            bad=Snapshot('failed','openaire','v3','now',old.query,'UNAVAILABLE','timeout',[],[],{},'sha256:failed')
            ci.verify('a',supplied_snapshot=bad)
            self.assertEqual(ws.load_analysis('a').latest_snapshot_id,old.snapshot_id)
