def test_consent_creates_record_and_sets_cookie(client):
    response = client.post("/consent")
    assert response.status_code == 200
    body = response.json()
    assert body["consented"] is True
    assert "session_id" in body
    assert "realdoor_session" in response.cookies


def test_consent_is_idempotent_per_session(client):
    from db import get_db
    from main import app
    from models import AuditLogRecord, ConsentRecord

    first = client.post("/consent")
    second = client.post("/consent")
    session_id = first.json()["session_id"]
    assert session_id == second.json()["session_id"]

    db = next(app.dependency_overrides[get_db]())
    assert db.query(ConsentRecord).filter_by(session_id=session_id).count() == 1
    assert (
        db.query(AuditLogRecord)
        .filter_by(session_id=session_id, action="consent_given")
        .count()
        == 1
    )
