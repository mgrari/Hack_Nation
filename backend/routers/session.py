import os

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from db import get_db
from models import AuditLogRecord, ConsentRecord, DocumentRecord, FieldRecord, SessionRecord
from session_cookie import COOKIE_NAME, get_or_create_session

router = APIRouter()


@router.delete("/session")
def delete_session(
    response: Response,
    session_id: str = Depends(get_or_create_session),
    db: Session = Depends(get_db),
):
    documents = db.query(DocumentRecord).filter_by(session_id=session_id).all()
    for doc in documents:
        if os.path.exists(doc.encrypted_path):
            try:
                os.remove(doc.encrypted_path)
            except OSError:
                pass
        db.query(FieldRecord).filter_by(document_id=doc.id).delete()
        db.delete(doc)

    db.query(ConsentRecord).filter_by(session_id=session_id).delete()
    db.query(AuditLogRecord).filter_by(session_id=session_id).delete()
    db.query(SessionRecord).filter_by(id=session_id).delete()
    db.commit()

    response.delete_cookie(COOKIE_NAME)
    return {"deleted": True}
