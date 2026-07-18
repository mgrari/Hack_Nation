import json
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "rules" / "mtsp_boston-cambridge_2026.json"
META_PATH = Path(__file__).parent.parent / "data" / "rules" / "mtsp_boston-cambridge_2026.meta.json"


def load_mtsp_limits() -> dict:
    with open(DATA_PATH) as f:
        rows = json.load(f)
    row = rows[0]  # every row shares identical metro-level limits

    with open(META_PATH) as f:
        meta = json.load(f)

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
