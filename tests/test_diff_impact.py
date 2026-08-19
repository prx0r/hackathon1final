import json,unittest
from pathlib import Path
from patala_research_ci.model import Snapshot,TrackedClaim,SemanticDiff
from patala_research_ci.diff import diff_snapshots
from patala_research_ci.impact import compute_impact

FIX=Path(__file__).resolve().parents[1]/'fixtures'/'demo'

class DiffImpactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=Snapshot.from_dict(json.loads((FIX/'baseline_snapshot.json').read_text()))
        cls.new=Snapshot.from_dict(json.loads((FIX/'current_snapshot.json').read_text()))
        d=json.loads((FIX/'claims.json').read_text())
        cls.claims=[TrackedClaim.from_dict(x) for x in d['claims']]

    def test_semantic_diff(self):
        d=diff_snapshots('a',self.old,self.new)
        self.assertEqual(d.summary.get('ENTITY_ADDED'),1)
        self.assertEqual(d.summary.get('RELATION_REMOVED'),1)
        self.assertEqual(d.summary.get('FIELD_CHANGED'),1)

    def test_claim_specific_impact(self):
        d=diff_snapshots('a',self.old,self.new)
        i=compute_impact('a',d,self.claims)
        states={x.claim_id:x.state for x in i.claims}
        self.assertEqual(states['claim:dataset-linkage'],'RECOMPUTE_REQUIRED')
        self.assertEqual(states['claim:open-access'],'RECOMPUTE_REQUIRED')
        self.assertEqual(states['claim:s2-dataset'],'RECOMPUTE_REQUIRED')

    def test_unrelated_field_does_not_trigger_manual_relation_claim(self):
        d=diff_snapshots('a',self.old,self.new)
        claim=[x for x in self.claims if x.claim_id=='claim:s2-dataset'][0]
        i=compute_impact('a',d,[claim])
        self.assertEqual(len(i.claims[0].change_ids),1)

    def test_partial_enrichment_never_fabricates_relation_removal(self):
        partial=Snapshot.from_dict(self.new.to_dict())
        partial.snapshot_id='partial'
        partial.source_status='PARTIAL'
        partial.source_error='ScholeXplorer timeout'
        partial.relations=[]
        d=diff_snapshots('a',self.old,partial)
        self.assertEqual(d.summary.get('SOURCE_PARTIAL'),1)
        self.assertFalse(any(c.kind=='RELATION_REMOVED' for c in d.changes))
        relation_claim=[x for x in self.claims if x.claim_id=='claim:s2-dataset'][0]
        open_claim=[x for x in self.claims if x.claim_id=='claim:open-access'][0]
        i=compute_impact('a',d,[relation_claim,open_claim])
        states={x.claim_id:x.state for x in i.claims}
        self.assertEqual(states['claim:s2-dataset'],'BLOCKED')
        # Query membership/field-only claims can still use the healthy primary Graph plane.
        self.assertNotEqual(states['claim:open-access'],'BLOCKED')

    def test_source_failure_never_becomes_mass_deletion(self):
        bad=Snapshot('bad','openaire','v3','now',self.old.query,'UNAVAILABLE','timeout',[],[],{},'sha256:bad')
        d=diff_snapshots('a',self.old,bad)
        self.assertEqual(d.summary,{'SOURCE_UNAVAILABLE':1})
        self.assertFalse(any(c.kind=='ENTITY_REMOVED' for c in d.changes))
