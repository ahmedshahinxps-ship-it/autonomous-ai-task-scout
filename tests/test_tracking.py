import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import track

def report(urls):
    return {"candidates": [{"title": f"Task {i}", "url": url,
                            "source": "algora", "reward_usd": 25, "score": 60}
                           for i, url in enumerate(urls)]}

class ChangeTests(unittest.TestCase):
    def test_only_new_links(self):
        old = report(["https://github.com/a/b/issues/1"])
        new = report(["https://github.com/a/b/issues/1", "https://github.com/a/b/issues/2"])
        result = track.compare(new, old, 123)
        self.assertEqual(result["comparison_status"], "compared")
        self.assertEqual(result["newly_shortlisted_count"], 1)
        self.assertEqual(result["previous_run_id"], 123)
        self.assertEqual(result["newly_shortlisted"][0]["url"], "https://github.com/a/b/issues/2")
    def test_first_run_does_not_falsely_claim_new(self):
        result = track.compare(report(["https://github.com/a/b/issues/2"]), None, status="baseline")
        self.assertEqual(result["newly_shortlisted_count"], 0)
    def test_unavailable_reference_does_not_falsely_claim_new(self):
        result = track.compare(report(["https://github.com/a/b/issues/2"]), None, status="unavailable")
        self.assertEqual(result["newly_shortlisted_count"], 0)
    def test_deduplication(self):
        new = report(["https://github.com/a/b/issues/2", "https://github.com/a/b/issues/2"])
        result = track.compare(new, report([]))
        self.assertEqual(result["newly_shortlisted_count"], 1)
    def test_escaping(self):
        doc = track.compare(report(["https://github.com/a/b/issues/1"]), report([]))
        doc["newly_shortlisted"][0]["title"] = "<img src=x onerror=alert(1)>"
        rendered = track.html_report(doc)
        self.assertNotIn("<img src=x", rendered)
        self.assertIn("&lt;img", rendered)

if __name__ == "__main__":
    unittest.main()
