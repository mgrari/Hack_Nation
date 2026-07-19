import os

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from config import settings
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

    # autoflush is off (see db.py), so the db.delete(doc) calls above are only queued --
    # without an explicit flush here, the bulk deletes below would run before those
    # deletes hit the database, violating documents.session_id's foreign key to
    # sessions.id on Postgres (SQLite doesn't enforce FKs by default, so this was
    # invisible locally).
    db.flush()

    db.query(ConsentRecord).filter_by(session_id=session_id).delete()
    db.query(AuditLogRecord).filter_by(session_id=session_id).delete()
    db.query(SessionRecord).filter_by(id=session_id).delete()
    db.commit()

    # Match the attributes the cookie was set with so browsers actually clear it
    # (a Secure/SameSite=None cookie won't be removed by a bare delete in production).
    is_production = settings.environment == "production"
    response.delete_cookie(
        COOKIE_NAME,
        httponly=True,
        samesite="none" if is_production else "lax",
        secure=is_production,
    )
    return {"deleted": True}
