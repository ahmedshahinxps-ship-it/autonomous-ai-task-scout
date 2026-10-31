#!/usr/bin/env python3
"""Deterministic local CSV cleanup worker; no web, AI API, job submission or payment."""
import argparse
import csv
import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

EXPECTED = ("sku", "product_name", "price_usd")
HEADERS = {
    "sku": ("sku", "product id", "product_id", "item code"),
    "product_name": ("product_name", "product name", "name", "product"),
    "price_usd": ("price_usd", "price", "usd price", "unit price"),
}
MAX_FILE_BYTES = 2_000_000
MAX_RECORDS = 10000
DANGEROUS = ("=", "+", "-", "@", "\t", "\r")

def safe_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()

def safe_cell(value):
    value = safe_text(value)
    if value.startswith(DANGEROUS):
        raise ValueError("possible spreadsheet formula injection")
    return value

def price(value):
    raw = safe_text(value).replace("$", "").replace(",", "")
    try:
        number = Decimal(raw)
    except InvalidOperation:
        raise ValueError("invalid price")
    if not number.is_finite() or number < 0 or number > 1_000_000:
        raise ValueError("out-of-range price")
    if number.as_tuple().exponent < -2:
        raise ValueError("price contains more than two decimal places")
    return format(number, ".2f")

def process(input_path, output_dir):
    inp = Path(input_path)
    if not inp.is_file() or inp.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Missing or oversized input CSV")
    if inp.suffix.lower() != ".csv":
        raise ValueError("Input file must be CSV")
    data_hash = hashlib.sha256(inp.read_bytes()).hexdigest()
    with inp.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        source = reader.fieldnames
        if not source:
            raise ValueError("Missing CSV headers")
        mapped = {}
        for name, aliases in HEADERS.items():
            matches = [col for col in source if safe_text(col).lower() in aliases]
            if len(matches) != 1:
                raise ValueError("Each expected field must have exactly one matching source column: "+name)
            mapped[name] = matches[0]
        accepted = {}
        invalid = []
        duplicates = 0
        total = 0
        for row_number, row in enumerate(reader, start=2):
            total += 1
            if total > MAX_RECORDS:
                raise ValueError("Input exceeds maximum rows")
            try:
                if None in row or None in (row.get(mapped[k]) for k in EXPECTED):
                    raise ValueError("malformed CSV row")
                sku = safe_cell(row[mapped["sku"]]).upper()
                name = safe_cell(row[mapped["product_name"]])
                amount = price(row[mapped["price_usd"]])
                if not sku or not name:
                    raise ValueError("missing required field")
                normalized = {"sku":sku, "product_name":name, "price_usd":amount}
                if sku in accepted:
                    if accepted[sku] != normalized:
                        invalid.append({"line":row_number,"reason":"duplicate SKU with conflicting data"})
                    else:
                        duplicates += 1
                    continue
                accepted[sku] = normalized
            except ValueError as exc:
                invalid.append({"line":row_number,"reason":str(exc)})
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path=out/"cleaned_catalogue.csv"
    with csv_path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=EXPECTED)
        writer.writeheader()
        writer.writerows(accepted.values())
    result={
        "mode":"DEMONSTRATION OR USER-SUPPLIED FILE; NOT A PAID BOUNTY",
        "task_type":"csv_product_catalogue_cleanup",
        "input_sha256":data_hash,
        "rows_read":total,"rows_accepted":len(accepted),
        "exact_duplicates_removed":duplicates,"invalid_or_conflicting_rows":invalid,
        "validation":{"all_prices_nonnegative":True, "unique_skus":True, "output_schema":list(EXPECTED)},
        "submitted":False,"accepted_by_buyer":False,"revenue_usd":0,
    }
    (out/"worker_audit.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",default="examples/sample_products.csv")
    parser.add_argument("--output",default="output/work_sample")
    opts=parser.parse_args()
    result=process(opts.input,opts.output)
    print(f"CSV cleaned: {result['rows_accepted']} accepted, {result['exact_duplicates_removed']} duplicate, {len(result['invalid_or_conflicting_rows'])} rejected. No paid submissions.")
if __name__=="__main__":
    main()
