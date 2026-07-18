from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from calculator import calculate_income_vs_threshold
from db import get_db
from models import AuditLogRecord, DocumentRecord, FieldRecord
from session_cookie import get_or_create_session

router = APIRouter()


class CalculateRequest(BaseModel):
    household_size: int
    ami_tier: str = "60"


@router.post("/calculate")
def calculate(
    body: CalculateRequest,
    session_id: str = Depends(get_or_create_session),
    db: Session = Depends(get_db),
):
    confirmed_income_fields = (
        db.query(FieldRecord)
        .join(DocumentRecord, FieldRecord.document_id == DocumentRecord.id)
        .filter(
            DocumentRecord.session_id == session_id,
            FieldRecord.confirmed.is_(True),
            FieldRecord.field_name == "gross_pay",
        )
        .all()
    )
    if not confirmed_income_fields:
        raise HTTPException(
            status_code=400,
            detail="No confirmed gross_pay field found. Confirm a field first.",
        )

    annual_income = sum(float(f.confirmed_value) for f in confirmed_income_fields) * 12
    result = calculate_income_vs_threshold(annual_income, body.household_size, body.ami_tier)

    db.add(AuditLogRecord(session_id=session_id, action="calculated", rule_version=result["effective_date"]))
    db.commit()
    return result
