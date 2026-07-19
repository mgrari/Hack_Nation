import io
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from crypto import encrypt_bytes
from db import get_db
from extraction import DOCUMENT_TYPES, call_extraction_model, extract_text_from_pdf
from models import AuditLogRecord, ConsentRecord, DocumentRecord, FieldRecord
from session_cookie import get_or_create_session

router = APIRouter()

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "storage", "documents")
os.makedirs(STORAGE_DIR, exist_ok=True)


@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Depends(get_or_create_session),
    db: Session = Depends(get_db),
):
    consent = db.query(ConsentRecord).filter_by(session_id=session_id).first()
    if not consent:
        raise HTTPException(status_code=403, detail="Consent required before upload")

    raw_bytes = await file.read()
    doc_id = str(uuid.uuid4())
    encrypted = encrypt_bytes(raw_bytes)
    path = os.path.join(STORAGE_DIR, f"{doc_id}.enc")
    with open(path, "wb") as f:
        f.write(encrypted)

    document = DocumentRecord(
        id=doc_id,
        session_id=session_id,
        encrypted_path=path,
        content_type=file.content_type or "application/octet-stream",
    )

    if file.content_type == "application/pdf":
        try:
            text = extract_text_from_pdf(io.BytesIO(raw_bytes))
        except Exception:
            db.rollback()
            raise HTTPException(status_code=422, detail="Could not read this document")
    else:
        # Vision path for scanned images: extraction.py's OpenAI call is text-only for now;
        # image support is a documented v1.1 follow-up (design spec section "Cut for v1").
        text = ""

    client = OpenAI(api_key=settings.openai_api_key)
    try:
        result = call_extraction_model(client, text)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=502, detail="Extraction service unavailable")

    document.document_type = result.document_type
    db.add(document)

    # Safety-critical: never trust the model to self-police which fields belong to its
    # own detected document_type. Drop anything that leaked across types.
    allowed_fields = set(DOCUMENT_TYPES.get(result.document_type, []))

    fields_out = []
    for extracted in result.fields:
        if extracted.field_name not in allowed_fields:
            continue
        field_record = FieldRecord(
            document_id=doc_id,
            field_name=extracted.field_name,
            extracted_value=extracted.value,
            confidence=extracted.confidence,
            source_box=extracted.source_box.model_dump() if extracted.source_box else None,
            confirmed=False,
        )
        db.add(field_record)
        db.flush()
        fields_out.append(
            {
                "id": field_record.id,
                "field_name": extracted.field_name,
                "value": extracted.value,
                "confidence": extracted.confidence,
            }
        )

    db.add(AuditLogRecord(session_id=session_id, action="document_uploaded"))
    db.commit()
    return {"document_id": doc_id, "document_type": result.document_type, "fields": fields_out}


class FieldCorrection(BaseModel):
    value: str


@router.patch("/documents/{document_id}/fields/{field_name}")
def correct_field(
    document_id: str,
    field_name: str,
    body: FieldCorrection,
    session_id: str = Depends(get_or_create_session),
    db: Session = Depends(get_db),
):
    document = db.query(DocumentRecord).filter_by(id=document_id, session_id=session_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    field = db.query(FieldRecord).filter_by(document_id=document_id, field_name=field_name).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    field.confirmed_value = body.value
    field.confirmed = True
    field.corrected_at = datetime.utcnow()
    db.add(AuditLogRecord(session_id=session_id, action="field_corrected", field_name=field_name))
    db.commit()
    return {"field_name": field_name, "confirmed_value": field.confirmed_value, "confirmed": True}
