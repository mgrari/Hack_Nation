from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from calculator import calculate_income_vs_threshold
from checklist import evaluate_checklist
from db import get_db
from models import AuditLogRecord, ConsentRecord, DocumentRecord, FieldRecord
from packet_pdf import render_packet_pdf
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


@router.get("/packet")
def get_packet(
    household_size: int,
    ami_tier: str = "60",
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
    annual_income = float(confirmed_fields.get("gross_pay", 0)) * 12
    calculation = calculate_income_vs_threshold(annual_income, household_size, ami_tier)

    consent = db.query(ConsentRecord).filter_by(session_id=session_id).first()
    checklist_items = evaluate_checklist(confirmed_fields, consent is not None)

    pdf_bytes = render_packet_pdf(confirmed_fields, calculation, checklist_items)
    db.add(AuditLogRecord(session_id=session_id, action="packet_exported"))
    db.commit()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=realdoor-packet.pdf"},
    )
