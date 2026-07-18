def test_calculate_requires_confirmed_income(client):
    client.post("/consent")
    response = client.post("/calculate", json={"household_size": 4, "ami_tier": "60"})
    assert response.status_code == 400


def test_calculate_returns_threshold_with_confirmed_income(client):
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

    response = client.post("/calculate", json={"household_size": 4, "ami_tier": "60"})
    assert response.status_code == 200
    body = response.json()
    assert body["threshold"] == 102840
    assert body["confirmed_value"] == 90000  # 7500 * 12
    assert "eligible" not in str(body).lower()


def test_calculate_rejects_non_numeric_confirmed_value(client):
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
    db.commit()

    response = client.post("/calculate", json={"household_size": 4, "ami_tier": "60"})
    assert response.status_code == 400
    assert "gross_pay" in response.json()["detail"]
