#!/usr/bin/env python3
"""
fetch_hud_data.py — Pull real HUD housing data for RealDoor's rule corpus.

Fetches, for one metro area:
  - MTSP (Multifamily Tax Subsidy Project) Income Limits — REQUIRED source per the brief
  - Section 8 Income Limits (optional context)
  - Fair Market Rents (optional context)

Saves everything as JSON into data/rules/, ready to feed your RAG/rules corpus.

SETUP (one-time):
  1. Register for a free HUD USER API account + token:
     https://www.huduser.gov/hudapi/public/register
  2. Log in, click "Create New Token": https://www.huduser.gov/hudapi/public/login
  3. Put the token in your environment:
     export HUD_API_TOKEN="your_token_here"
  4. pip install requests

USAGE:
  python fetch_hud_data.py --metro "Boston-Cambridge" --year 2026
  python fetch_hud_data.py --metro "Boston-Cambridge" --year 2026 --include-fmr

If your metro name matches more than one HUD area, the script prints all
matches and asks you to re-run with a more specific --metro string or the
exact --cbsa-code.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Missing dependency. Run: pip install requests")

BASE = "https://www.huduser.gov/hudapi/public"
DATA_DIR = Path(__file__).parent / "data" / "rules"


def get_token() -> str:
    token = os.environ.get("HUD_API_TOKEN")
    if not token:
        sys.exit(
            "HUD_API_TOKEN is not set.\n"
            "Register for a free token at https://www.huduser.gov/hudapi/public/register\n"
            "then run: export HUD_API_TOKEN=\"your_token_here\""
        )
    return token


def api_get(path: str, token: str, params: dict | None = None) -> dict:
    r = requests.get(f"{BASE}/{path}", headers={"Authorization": f"Bearer {token}"}, params=params)
    if r.status_code == 401:
        sys.exit("HUD API rejected the token (401). Check HUD_API_TOKEN is current and valid.")
    r.raise_for_status()
    return r.json()


def find_metro(token: str, query: str) -> list[dict]:
    """Search HUD's metro area list for a name match."""
    result = api_get("fmr/listMetroAreas", token)
    areas = result.get("data", result) if isinstance(result, dict) else result
    query_l = query.lower()
    return [a for a in areas if query_l in a["area_name"].lower()]


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def save_json(obj: dict, filename: str) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / filename
    path.write_text(json.dumps(obj, indent=2))
    return path


def main():
    parser = argparse.ArgumentParser(description="Fetch HUD MTSP/IL/FMR data for RealDoor.")
    parser.add_argument("--metro", help="Metro area name to search for, e.g. 'Boston-Cambridge'")
    parser.add_argument("--cbsa-code", help="Exact HUD cbsa_code if you already know it, e.g. METRO14460M14460")
    parser.add_argument("--year", type=int, default=2026, help="Data year (default: 2026)")
    parser.add_argument("--include-il", action="store_true", help="Also fetch Section 8 Income Limits (optional context)")
    parser.add_argument("--include-fmr", action="store_true", help="Also fetch Fair Market Rents (optional context)")
    args = parser.parse_args()

    if not args.metro and not args.cbsa_code:
        sys.exit("Provide --metro \"name\" or --cbsa-code METRO#####M#####")

    token = get_token()

    if args.cbsa_code:
        cbsa_code = args.cbsa_code
        area_name = args.cbsa_code
    else:
        matches = find_metro(token, args.metro)
        if not matches:
            sys.exit(f"No HUD metro area matched '{args.metro}'. Try a shorter/different substring.")
        if len(matches) > 1:
            print(f"Multiple matches for '{args.metro}':")
            for m in matches:
                print(f"  {m['cbsa_code']}  —  {m['area_name']}")
            sys.exit("Re-run with --cbsa-code <one of the codes above> to pick a specific one.")
        cbsa_code = matches[0]["cbsa_code"]
        area_name = matches[0]["area_name"]
        print(f"Matched: {area_name}  ({cbsa_code})")

    slug = slugify(area_name)

    # Required: MTSP Income Limits
    print(f"Fetching MTSP income limits for {area_name}, year {args.year}...")
    mtsp = api_get(f"mtspil/data/{cbsa_code}", token, params={"year": args.year})
    path = save_json(mtsp, f"mtsp_income_limits_{slug}_{args.year}.json")
    print(f"Saved: {path}")

    # Optional: Section 8 Income Limits
    if args.include_il:
        print(f"Fetching Section 8 income limits for {area_name}, year {args.year}...")
        il = api_get(f"il/data/{cbsa_code}", token, params={"year": args.year})
        path = save_json(il, f"section8_income_limits_{slug}_{args.year}.json")
        print(f"Saved: {path}")

    # Optional: Fair Market Rents
    if args.include_fmr:
        print(f"Fetching Fair Market Rents for {area_name}, year {args.year}...")
        fmr = api_get(f"fmr/data/{cbsa_code}", token, params={"year": args.year})
        path = save_json(fmr, f"fair_market_rents_{slug}_{args.year}.json")
        print(f"Saved: {path}")

    print("\nDone. Note: HUD's LIHTC property database has no simple API endpoint —")
    print("download it manually as CSV from https://www.huduser.gov/portal/datasets/lihtc.html")
    print("(pick your state, export CSV, drop the file into data/rules/ or data/properties/).")


if __name__ == "__main__":
    main()
