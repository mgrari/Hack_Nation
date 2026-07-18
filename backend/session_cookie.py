from fastapi import Depends, Request, Response
from sqlalchemy.orm import Session

from db import get_db
from models import SessionRecord

COOKIE_NAME = "realdoor_session"


def get_or_create_session(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> str:
    session_id = request.cookies.get(COOKIE_NAME)
    if session_id:
        record = db.query(SessionRecord).filter_by(id=session_id).first()
        if record:
            return session_id

    record = SessionRecord()
    db.add(record)
    db.commit()
    db.refresh(record)
    response.set_cookie(COOKIE_NAME, record.id, httponly=True, samesite="lax")
    return record.id
