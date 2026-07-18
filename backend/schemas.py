from typing import Optional

from pydantic import BaseModel


class SourceBox(BaseModel):
    page: int
    x: float
    y: float
    width: float
    height: float


class ExtractedField(BaseModel):
    field_name: str
    value: Optional[str] = None
    confidence: float
    source_box: Optional[SourceBox] = None


class ExtractionResult(BaseModel):
    fields: list[ExtractedField]
