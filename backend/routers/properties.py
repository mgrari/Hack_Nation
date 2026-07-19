import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "rules" / "lihtc_boston-cambridge.json"

router = APIRouter()


@lru_cache
def _load_properties() -> list[dict]:
    return json.loads(DATA_PATH.read_text())


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
