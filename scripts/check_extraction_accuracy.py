#!/usr/bin/env python3
"""Run every synthetic pay stub through a live RealDoor backend and diff against gold fields.

Usage (backend must already be running, e.g. `uvicorn main:app --port 8000` from backend/):
  python scripts/check_extraction_accuracy.py --base-url http://localhost:8000
"""
import argparse
import json
from pathlib import Path

import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--docs-dir", default="data/synthetic_docs")
    args = parser.parse_args()

    session = requests.Session()
    session.post(f"{args.base_url}/consent")

    docs_dir = Path(args.docs_dir)
    total_fields = 0
    correct_fields = 0

    for pdf_path in sorted(docs_dir.glob("paystub_*.pdf")):
        gold_path = pdf_path.with_suffix("").with_suffix(".gold.json")
        if not gold_path.exists():
            continue
        gold = json.loads(gold_path.read_text())

        with open(pdf_path, "rb") as f:
            response = session.post(
                f"{args.base_url}/documents",
                files={"file": (pdf_path.name, f, "application/pdf")},
            )
        response.raise_for_status()
        extracted = {f["field_name"]: f["value"] for f in response.json()["fields"]}

        for field_name, gold_value in gold.items():
            if not gold_value:
                continue
            total_fields += 1
            if extracted.get(field_name) == gold_value:
                correct_fields += 1
            else:
                print(f"{pdf_path.name}: {field_name} — expected {gold_value!r}, got {extracted.get(field_name)!r}")

    accuracy = correct_fields / total_fields if total_fields else 0
    print(f"\nField-level accuracy: {correct_fields}/{total_fields} = {accuracy:.1%}")


if __name__ == "__main__":
    main()
