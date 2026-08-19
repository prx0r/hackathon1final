import unittest
from patala_research_ci.canonical import digest_json

class CanonicalTests(unittest.TestCase):
    def test_dict_order_stable(self):
        self.assertEqual(digest_json({'b':2,'a':1}), digest_json({'a':1,'b':2}))

    def test_list_order_preserved(self):
        self.assertNotEqual(digest_json({'a':[1,2]}), digest_json({'a':[2,1]}))

    def test_transport_fields_can_be_dropped(self):
        a={'header':{'queryTime':12,'numFound':3},'x':1}
        b={'header':{'queryTime':99,'numFound':3},'x':1}
        self.assertEqual(digest_json(a,drop_volatile=True),digest_json(b,drop_volatile=True))
