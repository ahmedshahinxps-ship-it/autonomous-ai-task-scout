import datetime as dt
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import vet
NOW=dt.datetime(2026,10,31,tzinfo=dt.timezone.utc)

def lead(title='Update README guide',url='https://github.com/test-org/test-repo/issues/123'):
    return {'title':title,'url':url,'reward_usd':50}

def good(*_):
    return {'state':'open','locked':False,'assignees':[],'comments':2,
            'created_at':'2026-08-01T00:00:00Z','updated_at':'2026-10-01T00:00:00Z'}

class VetTests(unittest.TestCase):
    def test_safe_hosts(self):
        self.assertEqual(vet.issue_key(lead()['url']),('test-org','test-repo',123))
        self.assertEqual(vet.issue_key('https://oss.issuehunt.io/r/owner/repo/issues/8'),('owner','repo',8))
        self.assertIsNone(vet.issue_key('https://evil.example/a/b/issues/1'))
        self.assertIsNone(vet.issue_key('https://github.com/../x/issues/1'))
    def test_title_first(self):
        self.assertEqual(vet.classification('Write README documentation'),'documentation')
        self.assertEqual(vet.classification('Clean CSV dataset'),'data')
        self.assertEqual(vet.classification('Workable Integration'),'complex')
        self.assertEqual(vet.classification('Financial analysis dashboard'),'complex')
    def test_good(self):
        x=vet.vet_one(lead(),fetcher=good,now=NOW)
        self.assertEqual(x['state'],'preliminary-review')
        self.assertEqual(x['payment'],'NOT VERIFIED')
        self.assertEqual(x['ai_submissions'],'NOT VERIFIED')
    def test_locked(self):
        def blocked(*_):
            x=good();x['locked']=True;x['assignees']=[{'login':'somebody'}];return x
        self.assertEqual(vet.vet_one(lead(),fetcher=blocked,now=NOW)['state'],'skip')
    def test_old(self):
        def old(*_):
            x=good();x['created_at']='2020-01-01T00:00:00Z';return x
        self.assertEqual(vet.vet_one(lead(),fetcher=old,now=NOW)['state'],'skip')
    def test_no_network_for_complex(self):
        def fail(*_):raise AssertionError('No request should occur')
        self.assertEqual(vet.vet_one(lead('Implement dashboard'),fetcher=fail)['state'],'unverified')
    def test_cap(self):
        x=vet.vet_report({'candidates':[lead()]*10},max_checks=2,fetcher=good,now=NOW)
        self.assertEqual(x['issues_checked'],2)
        self.assertIn('NO tasks are approved',x['notice'])
    def test_escaped_output(self):
        x=vet.vet_report({'candidates':[lead('<script>alert(1)</script> README')]},
                         fetcher=good,now=NOW)
        page=vet.make_html(x)
        self.assertNotIn('<script>alert(1)</script>',page)
        self.assertIn('&lt;script&gt;',page)

if __name__=='__main__':unittest.main()
