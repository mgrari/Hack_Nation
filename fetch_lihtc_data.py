#!/usr/bin/env python3
"""
fetch_lihtc_data.py — Pull HUD LIHTC property locations into RealDoor's Discover data.

Source: HUD LIHTC Database (https://www.huduser.gov/portal/datasets/lihtc/property.html),
downloaded manually as LIHTCPUB.xlsx (openpyxl can't parse this file's malformed XML;
python-calamine can). Locations only — no vacancy, rent, or eligibility data exists in
this dataset, so none is emitted here.

USAGE:
  pip install python-calamine
  python fetch_lihtc_data.py --xlsx /path/to/LIHTCPUB.xlsx
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from python_calamine import CalamineWorkbook
except ImportError:
    sys.exit("Missing dependency. Run: pip install python-calamine")

DATA_DIR = Path(__file__).parent / "data" / "rules"
MTSP_CORPUS = DATA_DIR / "mtsp_boston-cambridge_2026.json"
OUT_PATH = DATA_DIR / "lihtc_boston-cambridge.json"


def metro_towns() -> set[str]:
    """The Boston-Cambridge-Quincy MA-NH HUD metro is already frozen via the MTSP
    corpus (114 towns) -- reuse that exact town list so Discover covers the same
    metro as the rest of the app, not a narrower ad-hoc one."""
    rows = json.loads(MTSP_CORPUS.read_text())
    return {re.sub(r"\s+(city|town)$", "", t).strip().upper() for t in {r["county_town_name"] for r in rows}}


def main():
    p = argparse.ArgumentParser(description="Filter HUD LIHTC properties to the frozen Boston-Cambridge metro.")
    p.add_argument("--xlsx", required=True, help="Path to the downloaded LIHTCPUB.xlsx")
    args = p.parse_args()

    towns = metro_towns()
    wb = CalamineWorkbook.from_path(args.xlsx)
    rows = wb.get_sheet_by_index(0).to_python()
    header = rows[0]
    idx = {h: i for i, h in enumerate(header)}

    # HUD uses 8888/9999 as "not available" sentinels in numeric fields, not real values.
    NOT_AVAILABLE = {8888, 9999}

    def clean_int(value):
        if value in ("", None):
            return None
        value = int(value)
        return None if value in NOT_AVAILABLE else value

    properties = []
    for r in rows[1:]:
        if r[idx["proj_st"]] != "MA":
            continue
        if str(r[idx["proj_cty"]]).upper() not in towns:
            continue
        properties.append(
            {
                "project": r[idx["project"]],
                "address": r[idx["proj_add"]],
                "town": r[idx["proj_cty"]],
                "zip": r[idx["proj_zip"]],
                "n_units": clean_int(r[idx["n_units"]]),
                "yr_pis": clean_int(r[idx["yr_pis"]]),
            }
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(properties, indent=2))
    print(f"Matched {len(properties)} propert(y/ies). Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
