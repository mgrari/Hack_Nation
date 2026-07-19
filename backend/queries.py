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


def get_confirmed_documents(db: Session, session_id: str) -> list[dict]:
    """Session's documents with their confirmed fields, shaped for readiness.evaluate_readiness()."""
    documents = db.query(DocumentRecord).filter(DocumentRecord.session_id == session_id).all()
    fields_by_document_id: dict[str, list[FieldRecord]] = {}
    confirmed_fields = (
        db.query(FieldRecord)
        .join(DocumentRecord, FieldRecord.document_id == DocumentRecord.id)
        .filter(DocumentRecord.session_id == session_id, FieldRecord.confirmed.is_(True))
        .all()
    )
    for f in confirmed_fields:
        fields_by_document_id.setdefault(f.document_id, []).append(f)

    return [
        {
            "document_type": doc.document_type,
            "fields": [
                {
                    "field_name": f.field_name,
                    "value": f.confirmed_value,
                    "source_box": f.source_box,
                }
                for f in fields_by_document_id.get(doc.id, [])
            ],
        }
        for doc in documents
    ]
