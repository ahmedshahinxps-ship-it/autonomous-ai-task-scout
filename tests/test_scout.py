import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import scout
def fixture():
    return {"title":"Fix README documentation","url":"https://example.org/task","content_text":"docs guide","tags":["docs"],"_jobbi":{"lane":"agent","claims_open":True,"reward":{"amount":50,"currency":"USD"},"payment_state":"escrowed","acceptance_type":"machine"}}
class ScoutTests(unittest.TestCase):
    def test_candidate(self):
        x=scout.inspect(fixture());self.assertEqual(x["reward_usd"],50)
        self.assertEqual(x["automated_submission_permitted"],"NOT VERIFIED")
    def test_currency(self):
        x=fixture();x["_jobbi"]["reward"]["currency"]="USDC";self.assertIsNone(scout.inspect(x))
    def test_closed(self):
        x=fixture();x["_jobbi"]["claims_open"]=False;self.assertIsNone(scout.inspect(x))
    def test_human(self):
        x=fixture();x["_jobbi"]["lane"]="human";self.assertIsNone(scout.inspect(x))
    def test_expired(self):
        x=fixture();x["_jobbi"]["expires"]="2020-01-01T00:00:00Z";self.assertIsNone(scout.inspect(x))
    def test_unsafe_url(self):
        x=fixture();x["url"]="javascript:alert(1)";self.assertIsNone(scout.inspect(x))
    def test_html_escapes(self):
        x=fixture();x["title"]="<script>alert(1)</script>"
        result=scout.html_report(scout.report([x]),True)
        self.assertNotIn("<script>alert(1)</script>",result)
        self.assertIn("&lt;script&gt;",result)
    def test_report_read_only(self):
        r=scout.report([fixture()])
        self.assertFalse(r["submissions_enabled"])
        self.assertFalse(r["payments_enabled"])
if __name__=="__main__":unittest.main()
