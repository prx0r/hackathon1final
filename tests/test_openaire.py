import unittest
from patala_research_ci.model import QuerySpec
from patala_research_ci.openaire import GraphV3Client,GraphV4Client,ScholeXplorerV3Client,BrokerClient
from patala_research_ci.source import FunctionTransport

class OpenAIREAdapterTests(unittest.TestCase):
    def test_v3_parameters(self):
        seen={}
        def h(url,p):
            seen.update({'url':url,'p':p}); return {'header':{'numFound':1},'results':[{'id':'x','type':'software','mainTitle':'X'}]}
        r=GraphV3Client(FunctionTransport(h)).search(QuerySpec(search='agent memory',filters={'type':'software'},page_size=7))
        self.assertEqual(r.status,'OK'); self.assertEqual(seen['p']['pageSize'],7); self.assertEqual(seen['p']['search'],'agent memory')
        self.assertTrue(seen['url'].endswith('/research-products'))

    def test_v4_unified_filter(self):
        seen={}
        def h(url,p): seen.update(p); return {'header':{},'results':[]}
        GraphV4Client(FunctionTransport(h)).search(QuerySpec(api_version='v4',filters={'type':'software','from_publication_year':2024},select=['id','mainTitle']))
        self.assertIn('type:software',seen['filter']); self.assertIn('from_publication_year:2024',seen['filter']); self.assertEqual(seen['select'],'id,mainTitle')

    def test_v3_current_author_shape(self):
        payload={"header":{"numFound":1},"results":[{
          "id":"doi_dedup___::x","type":"publication","mainTitle":"A study",
          "author":[{"fullName":"Ada Example","pid":{"id":{"scheme":"orcid","value":"0000-0001-2345-6789"}}}],
          "bestAccessRight":{"label":"Open Access"},"pid":[{"scheme":"doi","value":"10.1/example"}]
        }]}
        r=GraphV3Client(FunctionTransport(lambda u,p:payload)).search(QuerySpec())
        item=r.items[0]
        self.assertEqual(item["title"],"A study")
        self.assertEqual(item["authors"][0]["orcid"],"0000-0001-2345-6789")
        self.assertEqual(item["access_right"],"Open Access")
        self.assertEqual(item["pids"][0]["value"],"10.1/example")

    def test_scholexplorer_normalization(self):
        payload={'currentPage':0,'totalLinks':1,'totalPages':1,'result':[{
          'RelationshipType':{'Name':'IsRelatedTo','SubType':'cites'},
          'source':{'Identifier':[{'ID':'10.a/s'}],'Type':'Software'},
          'target':{'Identifier':[{'ID':'10.a/d'}],'Type':'Dataset'}
        }]}
        r=ScholeXplorerV3Client(FunctionTransport(lambda u,p:payload)).links(source_pid='10.a/s')
        self.assertEqual(r.relations[0]['relation'],'Cites'); self.assertEqual(r.relations[0]['relationship_name'],'IsRelatedTo'); self.assertEqual(r.relations[0]['target_type'],'Dataset')

    def test_broker_subscription_url(self):
        seen={}
        def h(url,p): seen['url']=url;seen['p']=p;return {'subscriptions':[{'id':'s'}]}
        r=BrokerClient(FunctionTransport(h)).subscriptions('x@example.org')
        self.assertEqual(r.status,'OK'); self.assertEqual(seen['p']['email'],'x@example.org')
