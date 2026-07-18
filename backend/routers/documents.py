import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from openai import OpenAI
from sqlalchemy.orm import Session

from config import settings
from crypto import encrypt_bytes
from db import get_db
from extraction import call_extraction_model, extract_text_from_pdf
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
    db.add(document)

    if file.content_type == "application/pdf":
        tmp_path = f"/tmp/{doc_id}.pdf"
        with open(tmp_path, "wb") as f:
            f.write(raw_bytes)
        text = extract_text_from_pdf(tmp_path)
        os.remove(tmp_path)
    else:
        # Vision path for scanned images: extraction.py's OpenAI call is text-only for now;
        # image support is a documented v1.1 follow-up (design spec section "Cut for v1").
        text = ""

    client = OpenAI(api_key=settings.openai_api_key)
    result = call_extraction_model(client, text)

    fields_out = []
    for extracted in result.fields:
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
    return {"document_id": doc_id, "fields": fields_out}
