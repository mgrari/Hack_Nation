import io
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from crypto import decrypt_bytes, encrypt_bytes
from db import get_db
from extraction import (
    DOCUMENT_TYPES,
    call_extraction_model,
    call_extraction_model_from_image,
    extract_text_from_pdf,
    locate_bbox,
    render_pdf_page_to_png,
)
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
        original_filename=file.filename,
    )

    is_pdf = file.content_type == "application/pdf"
    is_image = file.content_type in ("image/jpeg", "image/png")
    if not is_pdf and not is_image:
        db.rollback()
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Upload a PDF, JPG, or PNG.",
        )

    text = ""
    if is_pdf:
        try:
            text = extract_text_from_pdf(io.BytesIO(raw_bytes))
        except Exception:
            db.rollback()
            raise HTTPException(status_code=422, detail="Could not read this document")

    client = OpenAI(api_key=settings.openai_api_key)
    try:
        if text.strip():
            # Real text layer present (typical for a text-based PDF) -- cheaper and more
            # reliable than vision, use it.
            result = call_extraction_model(client, text)
        elif is_pdf:
            # No text layer (scanned/rasterized PDF page) -- fall back to reading the
            # rendered page image directly instead of refusing the upload.
            image_bytes = render_pdf_page_to_png(raw_bytes, page=1)
            result = call_extraction_model_from_image(client, image_bytes, "image/png")
        else:
            # Direct photo/screenshot upload (JPG/PNG) -- always goes through vision.
            result = call_extraction_model_from_image(client, raw_bytes, file.content_type)
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
        source_box = locate_bbox(raw_bytes, page=1, text=extracted.value) if is_pdf else None
        field_record = FieldRecord(
            document_id=doc_id,
            field_name=extracted.field_name,
            extracted_value=extracted.value,
            confidence=extracted.confidence,
            source_box=source_box,
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


@router.get("/documents")
def list_documents(
    session_id: str = Depends(get_or_create_session),
    db: Session = Depends(get_db),
):
    """Every document uploaded so far this session, oldest first, with each field's
    current value (confirmed_value once confirmed, otherwise the extracted value) --
    restores the Profile page's full upload history on page revisit."""
    documents = (
        db.query(DocumentRecord)
        .filter_by(session_id=session_id)
        .order_by(DocumentRecord.uploaded_at.asc())
        .all()
    )
    result = []
    for document in documents:
        fields = db.query(FieldRecord).filter_by(document_id=document.id).all()
        result.append(
            {
                "document_id": document.id,
                "document_type": document.document_type,
                "filename": document.original_filename,
                "fields": [
                    {
                        "id": f.id,
                        "field_name": f.field_name,
                        "value": f.confirmed_value if f.confirmed else f.extracted_value,
                        "confidence": f.confidence,
                        "confirmed": f.confirmed,
                    }
                    for f in fields
                ],
            }
        )
    return {"documents": result}


@router.get("/documents/{document_id}/file")
def get_document_file(
    document_id: str,
    session_id: str = Depends(get_or_create_session),
    db: Session = Depends(get_db),
):
    document = db.query(DocumentRecord).filter_by(id=document_id, session_id=session_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        with open(document.encrypted_path, "rb") as f:
            raw_bytes = decrypt_bytes(f.read())
    except Exception:
        raise HTTPException(status_code=404, detail="Stored file could not be read")

    filename = document.original_filename or f"{document_id}"
    return Response(
        content=raw_bytes,
        media_type=document.content_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: str,
    session_id: str = Depends(get_or_create_session),
    db: Session = Depends(get_db),
):
    document = db.query(DocumentRecord).filter_by(id=document_id, session_id=session_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if os.path.exists(document.encrypted_path):
        try:
            os.remove(document.encrypted_path)
        except OSError:
            pass

    db.query(FieldRecord).filter_by(document_id=document_id).delete()
    db.delete(document)
    db.add(AuditLogRecord(session_id=session_id, action="document_deleted"))
    db.commit()
    return {"deleted": True}


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
