from sqlalchemy.orm import Session

from models import DocumentRecord, FieldRecord


def get_confirmed_fields(db: Session, session_id: str) -> dict[str, str]:
    """Confirmed field values for a session, keyed by field_name."""
    fields = (
        db.query(FieldRecord)
        .join(DocumentRecord, FieldRecord.document_id == DocumentRecord.id)
        .filter(DocumentRecord.session_id == session_id, FieldRecord.confirmed.is_(True))
        .all()
    )
    return {f.field_name: f.confirmed_value for f in fields}
