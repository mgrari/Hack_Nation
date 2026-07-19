import io
import os


def test_delete_session_removes_data_and_cookie(client, monkeypatch):
    from schemas import ExtractedField, ExtractionResult

    def fake_extraction_call(_client, _text):
        return ExtractionResult(
            document_type="pay_stub",
            fields=[ExtractedField(field_name="gross_pay", value="7000", confidence=0.6)],
        )

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


def test_session_cookie_is_persistent_with_max_age(client):
    response = client.post("/consent")
    set_cookie = response.headers["set-cookie"].lower()
    # A persistent cookie (has Max-Age) survives browser close, so a returning renter
    # keeps the same session instead of getting a fresh one.
    assert "max-age=" in set_cookie


def test_returning_session_keeps_prior_documents(client, monkeypatch):
    """Same device/browser returning later (persistent cookie still in the jar) reuses
    the same session and still sees documents uploaded earlier."""
    import io

    from schemas import ExtractedField, ExtractionResult

    def fake_extraction_call(_client, _text):
        return ExtractionResult(
            document_type="pay_stub",
            fields=[ExtractedField(field_name="gross_pay", value="7000", confidence=0.6)],
        )

    monkeypatch.setattr("routers.documents.call_extraction_model", fake_extraction_call)
    monkeypatch.setattr("routers.documents.extract_text_from_pdf", lambda path: "text")

    client.post("/consent")
    session_id = client.cookies.get("realdoor_session")

    upload = client.post(
        "/documents",
        files={"file": ("paystub.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )
    document_id = upload.json()["document_id"]

    # A later visit -- same persistent cookie -- must resolve to the same session and
    # return the previously uploaded document.
    listing = client.get("/documents")
    assert listing.status_code == 200
    assert client.cookies.get("realdoor_session") == session_id
    returned_ids = [d["document_id"] for d in listing.json()["documents"]]
    assert document_id in returned_ids
