import json
from datetime import datetime, timedelta

import pytest


def test_load_gold_checklist_missing_file_raises_clear_error(tmp_path, monkeypatch):
    import checklist

    monkeypatch.setattr(checklist, "CHECKLIST_PATH", tmp_path / "does_not_exist.json")

    with pytest.raises(FileNotFoundError, match="does_not_exist.json"):
        checklist.load_gold_checklist()


def test_load_gold_checklist_malformed_json_raises_clear_error(tmp_path, monkeypatch):
    import checklist

    bad_data = tmp_path / "bad.json"
    bad_data.write_text("{not valid json")
    monkeypatch.setattr(checklist, "CHECKLIST_PATH", bad_data)

    with pytest.raises(json.JSONDecodeError, match="bad.json"):
        checklist.load_gold_checklist()


def test_evaluate_checklist_non_iso_date_degrades_to_missing():
    from checklist import evaluate_checklist

    results = evaluate_checklist(confirmed_fields={"pay_date": "not-a-date"}, consent_given=True)
    by_id = {item["id"]: item["status"] for item in results}

    assert by_id["pay_stub"] == "missing"
    assert by_id["consent_form"] == "present"


def test_evaluate_checklist_flags_missing_and_expired():
    from checklist import evaluate_checklist

    old_date = (datetime.utcnow() - timedelta(days=90)).date().isoformat()
    results = evaluate_checklist(confirmed_fields={"pay_date": old_date}, consent_given=True)
    by_id = {item["id"]: item["status"] for item in results}

    assert by_id["pay_stub"] == "expired"
    assert by_id["consent_form"] == "present"
    assert by_id["photo_id"] == "missing"


def test_evaluate_checklist_present_for_recent_pay_stub():
    from checklist import evaluate_checklist

    recent_date = datetime.utcnow().date().isoformat()
    results = evaluate_checklist(confirmed_fields={"pay_date": recent_date}, consent_given=False)
    by_id = {item["id"]: item["status"] for item in results}

    assert by_id["pay_stub"] == "present"
    assert by_id["consent_form"] == "missing"


def test_get_checklist_endpoint(client):
    client.post("/consent")
    response = client.get("/checklist")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 5
    by_id = {item["id"]: item["status"] for item in body["items"]}
    assert by_id["consent_form"] == "present"
    assert by_id["pay_stub"] == "missing"


def test_get_packet_returns_pdf(client):
    from db import get_db
    from main import app
    from models import DocumentRecord, FieldRecord

    client.post("/consent")
    session_id = client.cookies.get("realdoor_session")

    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    doc = DocumentRecord(session_id=session_id, encrypted_path="unused", content_type="application/pdf")
    db.add(doc)
    db.commit()
    db.add(FieldRecord(document_id=doc.id, field_name="gross_pay", confirmed_value="7500", confirmed=True))
    db.add(FieldRecord(document_id=doc.id, field_name="pay_frequency", confirmed_value="monthly", confirmed=True))
    db.commit()

    response = client.get("/packet?household_size=4&ami_tier=60")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"


def test_get_packet_requires_confirmed_income(client):
    client.post("/consent")
    response = client.get("/packet?household_size=4&ami_tier=60")
    assert response.status_code == 400


def test_get_packet_rejects_non_numeric_confirmed_value(client):
    from db import get_db
    from main import app
    from models import DocumentRecord, FieldRecord

    client.post("/consent")
    session_id = client.cookies.get("realdoor_session")

    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    doc = DocumentRecord(session_id=session_id, encrypted_path="unused", content_type="application/pdf")
    db.add(doc)
    db.commit()
    db.add(FieldRecord(document_id=doc.id, field_name="gross_pay", confirmed_value="not-a-number", confirmed=True))
    db.add(FieldRecord(document_id=doc.id, field_name="pay_frequency", confirmed_value="monthly", confirmed=True))
    db.commit()

    response = client.get("/packet?household_size=4&ami_tier=60")
    assert response.status_code == 400
    assert "gross_pay" in response.json()["detail"]


def test_get_packet_requires_confirmed_pay_frequency(client):
    from db import get_db
    from main import app
    from models import DocumentRecord, FieldRecord

    client.post("/consent")
    session_id = client.cookies.get("realdoor_session")

    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    doc = DocumentRecord(session_id=session_id, encrypted_path="unused", content_type="application/pdf")
    db.add(doc)
    db.commit()
    db.add(FieldRecord(document_id=doc.id, field_name="gross_pay", confirmed_value="7500", confirmed=True))
    db.commit()

    response = client.get("/packet?household_size=4&ami_tier=60")
    assert response.status_code == 400
    assert "pay_frequency" in response.json()["detail"]
