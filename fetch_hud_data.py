#!/usr/bin/env python3
"""
fetch_hud_data.py — Pull HUD MTSP income-limit data into RealDoor's rule corpus.

No API token needed. Downloads HUD's official static FY2026 MTSP Income Limits
Excel file (published directly on huduser.gov, no login required) and pulls out
just the rows matching your metro area.

SETUP:
  pip install requests pandas openpyxl

USAGE:
  # First run — see how this year's file is actually laid out:
  python fetch_hud_data.py --list-columns

  # Then pull rows for your metro:
  python fetch_hud_data.py --area "Boston-Cambridge"
  python fetch_hud_data.py --area "Boston-Cambridge" --year 2025   # older year if needed
"""

import argparse
import sys
from pathlib import Path

try:
    import requests
    import pandas as pd
except ImportError:
    sys.exit("Missing dependencies. Run: pip install requests pandas openpyxl")

DATA_DIR = Path(__file__).parent / "data" / "rules"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; RealDoorBot/1.0)"}


def source_url(year: int) -> str:
    """HUD publishes one static national file per fiscal year at a predictable path."""
    yy = str(year)[-2:]
    return f"https://www.huduser.gov/portal/datasets/mtsp/mtsp{yy}/MTSP-Data-FY{yy}.xlsx"


def download(year: int) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dest = DATA_DIR / f"mtsp_national_fy{year}.xlsx"
    if dest.exists():
        print(f"Already have: {dest}")
        return dest
    url = source_url(year)
    print(f"Downloading {url} ...")
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    dest.write_bytes(r.content)
    print(f"Saved: {dest}")
    return dest


def main():
    p = argparse.ArgumentParser(description="Pull HUD MTSP income limits for one metro area.")
    p.add_argument("--area", help="Substring to search for, e.g. 'Boston-Cambridge'")
    p.add_argument("--year", type=int, default=2026)
    p.add_argument("--list-columns", action="store_true", help="Print columns + sample rows, then exit")
    args = p.parse_args()

    df = pd.read_excel(download(args.year), engine="openpyxl")

    if args.list_columns:
        print("Columns:", list(df.columns))
        print(df.head())
        return

    if not args.area:
        sys.exit("Provide --area \"name\" (or run --list-columns first to see how areas are labeled).")

    # Search every text column — HUD's exact area-name column varies by year,
    # so this doesn't assume one specific column name.
    text_cols = df.select_dtypes(include="object").columns
    mask = df[text_cols].apply(lambda c: c.astype(str).str.contains(args.area, case=False, na=False)).any(axis=1)
    matches = df[mask]

    if matches.empty:
        sys.exit(f"No rows matched '{args.area}'. Run --list-columns to check how areas are named.")

    slug = args.area.lower().replace(" ", "_").replace(",", "")
    out_path = DATA_DIR / f"mtsp_{slug}_{args.year}.json"
    matches.to_json(out_path, orient="records", indent=2)
    print(f"Matched {len(matches)} row(s). Saved: {out_path}")


if __name__ == "__main__":
    main()
