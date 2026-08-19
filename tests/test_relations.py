import unittest
from patala_research_ci.relations import canonical_relation, relation_key

class RelationTests(unittest.TestCase):
    def test_citation_inverse_collapses(self):
        a=canonical_relation('rp:C','IsCitedBy','paper:Y')
        b=canonical_relation('paper:Y','Cites','rp:C')
        self.assertEqual(a,b)
        self.assertEqual(a,{'source':'paper:Y','relation':'Cites','target':'rp:C'})
    def test_reference_inverse_collapses(self):
        self.assertEqual(canonical_relation('A','IsReferencedBy','B'),canonical_relation('B','References','A'))
if __name__=='__main__': unittest.main()
