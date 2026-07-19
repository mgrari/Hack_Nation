import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "rules" / "lihtc_boston-cambridge.json"
FMR_PATH = Path(__file__).parent.parent.parent / "data" / "rules" / "fmr_boston-cambridge_2026.json"
SAFMR_PATH = Path(__file__).parent.parent.parent / "data" / "rules" / "safmr_boston-cambridge_2026.json"

router = APIRouter()


@lru_cache
def _load_properties() -> list[dict]:
    properties = json.loads(DATA_PATH.read_text())
    safmr_by_zip = json.loads(SAFMR_PATH.read_text())
    for p in properties:
        p["safmr"] = safmr_by_zip.get(p["zip"])
    return properties


@router.get("/properties/fmr")
def get_fmr():
    """Metro-wide HUD Fair Market Rents -- market context only, not a per-property rent
    or availability signal (HUD doesn't publish either)."""
    return json.loads(FMR_PATH.read_text())


@router.get("/properties")
def list_properties(city: str | None = None, min_units: int | None = None):
    properties = _load_properties()
    if city:
        properties = [p for p in properties if p["town"].casefold() == city.casefold()]
    if min_units is not None:
        properties = [p for p in properties if (p["n_units"] or 0) >= min_units]
    return {"properties": properties}


@router.get("/properties/towns")
def list_towns():
    return {"towns": sorted({p["town"] for p in _load_properties()})}
