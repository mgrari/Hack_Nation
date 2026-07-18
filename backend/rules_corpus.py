import json
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "rules" / "mtsp_boston-cambridge_2026.json"
META_PATH = Path(__file__).parent.parent / "data" / "rules" / "mtsp_boston-cambridge_2026.meta.json"


def load_mtsp_limits() -> dict:
    try:
        with open(DATA_PATH) as f:
            rows = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"MTSP data file not found: {DATA_PATH}. "
            "Generate it by running fetch_hud_data.py (see backend/../fetch_hud_data.py)."
        )
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"MTSP data file is not valid JSON: {DATA_PATH} ({e.msg})", e.doc, e.pos
        )

    if not rows:
        raise ValueError(f"MTSP data file has no rows: {DATA_PATH}")
    row = rows[0]  # every row shares identical metro-level limits

    try:
        with open(META_PATH) as f:
            meta = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"MTSP meta file not found: {META_PATH}. "
            "This file is hand-created alongside the data file — see its own "
            "effective_date/source_url fields for what to fill in."
        )
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"MTSP meta file is not valid JSON: {META_PATH} ({e.msg})", e.doc, e.pos
        )

    limits = {
        size: {"50": row[f"lim50_26p{size}"], "60": row[f"Lim60_26p{size}"]}
        for size in range(1, 9)
    }

    return {
        "area_name": row["hud_area_name"],
        "median_income": row["median2026"],
        "limits": limits,
        "effective_date": meta["effective_date"],
        "source_url": meta["source_url"],
    }
