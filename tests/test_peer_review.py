import unittest
from patala_research_ci.peer_review import ReviewEvidenceSpan, make_finding, make_review, finding_to_evidence_packet

class PeerReviewTests(unittest.TestCase):
    def test_structured_contradiction_and_human_promotion(self):
        f=make_finding('claim:1','NEEDS_HUMAN_REVIEW','sources disagree',[
            ReviewEvidenceSpan('doi:1','supports','sha256:'+'1'*64),
            ReviewEvidenceSpan('doi:2','contradicts','sha256:'+'2'*64),
        ])
        r=make_review('paper:1',[f])
        self.assertTrue(f.digest.startswith('sha256:'))
        self.assertTrue(r.digest.startswith('sha256:'))
        p=finding_to_evidence_packet(f,['domain expert'])
        self.assertEqual(len(p.evidence),2)
        self.assertIn('finding_digest',p.acceptance)
        self.assertEqual(p.required_expertise,('domain expert',))

if __name__=='__main__': unittest.main()
