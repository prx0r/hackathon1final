import json,tempfile,unittest
from pathlib import Path
from patala_research_ci.ledger import Ledger
from patala_research_ci.model import Dependency,TrackedClaim,ResolutionCheck,ResolutionPlan,Snapshot
from patala_research_ci.verification import VerificationService,plan_hash

class LedgerVerificationTests(unittest.TestCase):
    def test_ledger_tamper_detection(self):
        with tempfile.TemporaryDirectory() as td:
            l=Ledger(Path(td)/'l.jsonl');l.append('a','x',{'v':1});l.append('b','x',{'v':2})
            self.assertTrue(l.verify()[0])
            lines=l.path.read_text().splitlines(); e=json.loads(lines[0]);e['payload']['v']=9;lines[0]=json.dumps(e)
            l.path.write_text('\n'.join(lines)+'\n')
            self.assertFalse(l.verify()[0])

    def test_frozen_plan_receipt(self):
        claim=TrackedClaim('c','count',[Dependency(kind='query_membership')],{'type':'count','where':{'field':'type','equals':'software'},'op':'>=','threshold':1})
        snap=Snapshot('s','openaire','v3','now',{},'OK',None,[{'id':'x','type':'software'}],[],{},'sha256:s')
        plan=ResolutionPlan('p','1','o',{'analysis_id':'a'},(ResolutionCheck('health','source_status_ok',{'expected':'OK'}),ResolutionCheck('compute','recompute_claim',{})))
        v=VerificationService();r=v.run(plan,claim,snap)
        self.assertTrue(v.verify_receipt(r,plan)[0]);self.assertEqual(r.plan_hash,plan_hash(plan))
        changed=ResolutionPlan('p','1','o',{'analysis_id':'a'},(ResolutionCheck('health','source_status_ok',{'expected':'PARTIAL'}),))
        self.assertFalse(v.verify_receipt(r,changed)[0])
