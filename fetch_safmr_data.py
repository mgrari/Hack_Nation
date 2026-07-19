#!/usr/bin/env python3
"""
fetch_safmr_data.py — Pull HUD Small Area Fair Market Rents for RealDoor's Discover data.

Source: HUD SAFMR dataset (https://www.huduser.gov/portal/datasets/fmr.html), downloaded
manually as fy2026_safmrs_revised.xlsx. Per-ZIP FMR, filtered to the ZIPs that already
appear in data/rules/lihtc_boston-cambridge.json -- market context only, not a live
asking rent or availability signal, and never tied to a specific unit.

USAGE:
  pip install python-calamine
  python fetch_safmr_data.py --xlsx /path/to/fy2026_safmrs_revised.xlsx
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from python_calamine import CalamineWorkbook
except ImportError:
    sys.exit("Missing dependency. Run: pip install python-calamine")

DATA_DIR = Path(__file__).parent / "data" / "rules"
LIHTC_PATH = DATA_DIR / "lihtc_boston-cambridge.json"
OUT_PATH = DATA_DIR / "safmr_boston-cambridge_2026.json"


def metro_zips() -> set[str]:
    properties = json.loads(LIHTC_PATH.read_text())
    return {p["zip"] for p in properties if p.get("zip")}


def main():
    p = argparse.ArgumentParser(description="Extract per-ZIP SAFMRs for this metro's LIHTC properties.")
    p.add_argument("--xlsx", required=True, help="Path to the downloaded SAFMR file")
    args = p.parse_args()

    zips = metro_zips()
    wb = CalamineWorkbook.from_path(args.xlsx)
    rows = wb.get_sheet_by_index(0).to_python()
    header = rows[0]
    idx = {h: i for i, h in enumerate(header)}
    zip_col = "ZIP\nCode"

    by_zip = {}
    for r in rows[1:]:
        z = r[idx[zip_col]]
        if z not in zips:
            continue
        by_zip[z] = {
            "fmr_0br": r[idx["SAFMR\n0BR"]],
            "fmr_1br": r[idx["SAFMR\n1BR"]],
            "fmr_2br": r[idx["SAFMR\n2BR"]],
            "fmr_3br": r[idx["SAFMR\n3BR"]],
            "fmr_4br": r[idx["SAFMR\n4BR"]],
        }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(by_zip, indent=2))
    print(f"Matched {len(by_zip)} of {len(zips)} ZIPs. Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
