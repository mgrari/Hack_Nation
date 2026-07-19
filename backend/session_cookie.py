from fastapi import Depends, Request, Response
from sqlalchemy.orm import Session

from config import settings
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
    is_production = settings.environment == "production"
    response.set_cookie(
        COOKIE_NAME,
        record.id,
        # max_age makes this a persistent cookie (survives browser close) instead of a
        # session cookie, so a returning renter keeps the same session and their prior
        # documents rather than starting over.
        max_age=settings.session_ttl_days * 24 * 60 * 60,
        httponly=True,
        samesite="none" if is_production else "lax",
        secure=is_production,
    )
    return record.id
