from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config import settings
from db import get_db
from models import AuditLogRecord, ConsentRecord
from session_cookie import get_or_create_session

router = APIRouter()


@router.post("/consent")
def give_consent(
    session_id: str = Depends(get_or_create_session),
    db: Session = Depends(get_db),
):
    existing = db.query(ConsentRecord).filter_by(session_id=session_id).first()
    if existing:
        return {
            "session_id": session_id,
            "consented": True,
            "consent_version": existing.consent_version,
        }

    record = ConsentRecord(session_id=session_id, consent_version=settings.consent_version)
    db.add(record)
    db.add(AuditLogRecord(session_id=session_id, action="consent_given"))
    db.commit()
    return {
        "session_id": session_id,
        "consented": True,
        "consent_version": settings.consent_version,
    }
