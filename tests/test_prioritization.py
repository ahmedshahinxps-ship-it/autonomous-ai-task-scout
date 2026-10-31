import datetime as dt
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import scout

NOW=dt.datetime(2026,10,31,tzinfo=dt.timezone.utc)

def item(source='algora', published='2026-10-30T08:00:00Z',
         title='Update README guide', body='Fix documentation'):
    return {
        'title':title,'content_text':body,
        'url':'https://github.com/example/project/issues/1',
        'date_published':published, 'tags':['docs'],
        '_jobbi':{'lane':'agent','claims_open':True,
                  'reward':{'amount':60,'currency':'USD','rail':'stripe'},
                  'payment_state':'escrowed','acceptance_type':'human-review',
                  'source':source,'payout_grade':'B'}
    }

class RankTests(unittest.TestCase):
    def test_recent_preferred_over_stale(self):
        recent=scout.inspect(item(),now=NOW)
        old=scout.inspect(item(published='2022-01-01T00:00:00Z'),now=NOW)
        self.assertGreater(recent['score'],old['score'])
        self.assertEqual(recent['age_days'],0)
        self.assertEqual(old['payment_rail'],'stripe')
        self.assertEqual(old['payout_grade'],'B')
    def test_algora_preferred_over_issuehunt_at_equal_age(self):
        self.assertGreater(scout.inspect(item('algora'),now=NOW)['score'],
                           scout.inspect(item('issuehunt'),now=NOW)['score'])
    def test_complex_title_penalised(self):
        plain=scout.inspect(item(),now=NOW)
        complex_=scout.inspect(item(title='Implement integration and update README guide'),now=NOW)
        self.assertLess(complex_['score'],plain['score'])
    def test_report_order_and_no_submissions(self):
        report=scout.report([item('issuehunt'),item('algora')],20)
        self.assertEqual(report['candidates'][0]['source'],'algora')
        self.assertFalse(report['submissions_enabled'])
    def test_invalid_publication_does_not_crash(self):
        self.assertIsNone(scout.inspect(item(published='not a date'),now=NOW)['age_days'])

if __name__=='__main__':unittest.main()
