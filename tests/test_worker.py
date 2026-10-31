import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import worker

class WorkerTests(unittest.TestCase):
    def create(self, folder, content):
        filename=folder/"input.csv"
        filename.write_text(content,encoding="utf-8")
        return filename
    def test_sample(self):
        path=Path(__file__).resolve().parents[1]/"examples"/"sample_products.csv"
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/"out"
            report=worker.process(path,output)
            self.assertEqual(report["rows_read"],8)
            self.assertEqual(report["rows_accepted"],3)
            self.assertEqual(report["exact_duplicates_removed"],1)
            self.assertEqual(len(report["invalid_or_conflicting_rows"]),4)
            self.assertEqual(report["revenue_usd"],0)
            self.assertFalse(report["submitted"])
            self.assertTrue((output/"cleaned_catalogue.csv").is_file())
            with (output/"cleaned_catalogue.csv").open(newline="") as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(rows[0],{"sku":"A101","product_name":"Electric Kettle","price_usd":"19.99"})
    def test_formula_injection(self):
        with self.assertRaises(ValueError):worker.safe_cell(' =SUM(1,1)')
        with self.assertRaises(ValueError):worker.safe_cell('@IMPORT')
    def test_invalid_prices(self):
        for v in ("","NaN","Infinity","-4","2.123","bad"):
            with self.subTest(v=v),self.assertRaises(ValueError):worker.price(v)
    def test_duplicate_conflict_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path=self.create(Path(temp),"sku,name,price\nA,Tea,1\nA,Tea,2\n")
            report=worker.process(path,Path(temp)/"out")
            self.assertEqual(report["rows_accepted"],1)
            self.assertEqual(len(report["invalid_or_conflicting_rows"]),1)
    def test_missing_headers(self):
        with tempfile.TemporaryDirectory() as temp:
            path=self.create(Path(temp),"unrelated,fields\nA,B\n")
            with self.assertRaises(ValueError):worker.process(path,Path(temp)/"out")
if __name__=="__main__":unittest.main()
