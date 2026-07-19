from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from calculator import annualize, calculate_income_vs_threshold, parse_confirmed_amount
from checklist import evaluate_checklist
from db import get_db
from models import AuditLogRecord, ConsentRecord
from packet_pdf import render_packet_pdf
from queries import get_confirmed_documents, get_confirmed_fields
from session_cookie import get_or_create_session

router = APIRouter()


@router.get("/checklist")
def get_checklist(
    session_id: str = Depends(get_or_create_session),
    db: Session = Depends(get_db),
):
    confirmed_fields = get_confirmed_fields(db, session_id)
    confirmed_documents = get_confirmed_documents(db, session_id)
    consent = db.query(ConsentRecord).filter_by(session_id=session_id).first()
    return {"items": evaluate_checklist(confirmed_fields, consent is not None, confirmed_documents)}


@router.get("/packet")
def get_packet(
    household_size: int,
    ami_tier: str = "60",
    session_id: str = Depends(get_or_create_session),
    db: Session = Depends(get_db),
):
    confirmed_fields = get_confirmed_fields(db, session_id)
    if "gross_pay" not in confirmed_fields:
        raise HTTPException(
            status_code=400,
            detail="No confirmed gross_pay field found. Confirm a field first.",
        )
    if "pay_frequency" not in confirmed_fields:
        raise HTTPException(
            status_code=400,
            detail="No confirmed pay_frequency field found. Confirm a field first.",
        )

    try:
        annual_income = annualize(parse_confirmed_amount(confirmed_fields["gross_pay"]), confirmed_fields["pay_frequency"])
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"gross_pay or pay_frequency field is invalid: {exc}",
        )
    calculation = calculate_income_vs_threshold(annual_income, household_size, ami_tier)

    confirmed_documents = get_confirmed_documents(db, session_id)
    consent = db.query(ConsentRecord).filter_by(session_id=session_id).first()
    checklist_items = evaluate_checklist(confirmed_fields, consent is not None, confirmed_documents)

    pdf_bytes = render_packet_pdf(confirmed_fields, calculation, checklist_items)
    db.add(AuditLogRecord(session_id=session_id, action="packet_exported"))
    db.commit()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=realdoor-packet.pdf"},
    )
