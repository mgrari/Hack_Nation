import io
import os


def test_delete_session_removes_data_and_cookie(client, monkeypatch):
    from schemas import ExtractedField, ExtractionResult

    def fake_extraction_call(_client, _text):
        return ExtractionResult(fields=[ExtractedField(field_name="gross_pay", value="7000", confidence=0.6)])

    monkeypatch.setattr("routers.documents.call_extraction_model", fake_extraction_call)
    monkeypatch.setattr("routers.documents.extract_text_from_pdf", lambda path: "text")

    client.post("/consent")
    session_id = client.cookies.get("realdoor_session")

    upload = client.post(
        "/documents",
        files={"file": ("paystub.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )
    assert upload.status_code == 200

    from models import AuditLogRecord, ConsentRecord, DocumentRecord, FieldRecord, SessionRecord

    db = client.session_local()
    document = db.query(DocumentRecord).filter_by(id=upload.json()["document_id"]).first()
    encrypted_path = document.encrypted_path
    document_id = document.id
    db.close()
    assert os.path.exists(encrypted_path)

    response = client.delete("/session")
    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert "realdoor_session" not in response.cookies

    assert not os.path.exists(encrypted_path)

    checklist = client.get("/checklist")
    checklist_by_id = {item["id"]: item["status"] for item in checklist.json()["items"]}
    assert checklist_by_id["consent_form"] == "missing"  # brand-new session, consent gone

    from db import get_db
    from main import app

    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    assert db.query(SessionRecord).filter_by(id=session_id).first() is None
    assert db.query(ConsentRecord).filter_by(session_id=session_id).first() is None
    assert db.query(DocumentRecord).filter_by(session_id=session_id).first() is None
    assert db.query(FieldRecord).filter_by(document_id=document_id).first() is None
    assert db.query(AuditLogRecord).filter_by(session_id=session_id).first() is None
    db.close()
