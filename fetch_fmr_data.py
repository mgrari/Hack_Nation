#!/usr/bin/env python3
"""
fetch_fmr_data.py — Pull HUD Fair Market Rents into RealDoor's Discover context.

Source: HUD FMR dataset (https://www.huduser.gov/portal/datasets/fmr.html), downloaded
manually as a county-level FY2026 FMR file (python-calamine reads it; openpyxl chokes on
HUD's export like it does on the LIHTC file). Optional market context only, per the
challenge brief -- FMRs are not live asking rents, application criteria, or availability.

USAGE:
  pip install python-calamine
  python fetch_fmr_data.py --xlsx /path/to/FY26_FMRs_revised.xlsx
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
MTSP_CORPUS = DATA_DIR / "mtsp_boston-cambridge_2026.json"
OUT_PATH = DATA_DIR / "fmr_boston-cambridge_2026.json"


def metro_hud_area_code() -> str:
    """Reuse the exact HUD area code already frozen via the MTSP corpus, so Fair Market
    Rents describe the same metro as everything else in the app."""
    rows = json.loads(MTSP_CORPUS.read_text())
    codes = {r["hud_area_code"] for r in rows}
    (code,) = codes  # MTSP corpus is frozen to one metro -- this must be a single value.
    return code


def main():
    p = argparse.ArgumentParser(description="Extract this metro's Fair Market Rents.")
    p.add_argument("--xlsx", required=True, help="Path to the downloaded county-level FMR file")
    args = p.parse_args()

    area_code = metro_hud_area_code()
    wb = CalamineWorkbook.from_path(args.xlsx)
    rows = wb.get_sheet_by_index(0).to_python()
    header = rows[0]
    idx = {h: i for i, h in enumerate(header)}

    match = next((r for r in rows[1:] if r[idx["hud_area_code"]] == area_code), None)
    if match is None:
        sys.exit(f"No rows matched hud_area_code {area_code!r}.")

    out = {
        "hud_area_code": area_code,
        "hud_area_name": match[idx["hud_area_name"]],
        "fmr_0br": match[idx["fmr_0"]],
        "fmr_1br": match[idx["fmr_1"]],
        "fmr_2br": match[idx["fmr_2"]],
        "fmr_3br": match[idx["fmr_3"]],
        "fmr_4br": match[idx["fmr_4"]],
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2))
    print(f"Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
