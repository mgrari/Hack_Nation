from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from checklist import evaluate_checklist
from db import get_db
from models import ConsentRecord, DocumentRecord, FieldRecord
from session_cookie import get_or_create_session

router = APIRouter()


@router.get("/checklist")
def get_checklist(
    session_id: str = Depends(get_or_create_session),
    db: Session = Depends(get_db),
):
    fields = (
        db.query(FieldRecord)
        .join(DocumentRecord, FieldRecord.document_id == DocumentRecord.id)
        .filter(DocumentRecord.session_id == session_id, FieldRecord.confirmed.is_(True))
        .all()
    )
    confirmed_fields = {f.field_name: f.confirmed_value for f in fields}
    consent = db.query(ConsentRecord).filter_by(session_id=session_id).first()
    return {"items": evaluate_checklist(confirmed_fields, consent is not None)}
