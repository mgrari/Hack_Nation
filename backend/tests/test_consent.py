def test_consent_creates_record_and_sets_cookie(client):
    response = client.post("/consent")
    assert response.status_code == 200
    body = response.json()
    assert body["consented"] is True
    assert "session_id" in body
    assert "realdoor_session" in response.cookies


def test_consent_is_idempotent_per_session(client):
    first = client.post("/consent")
    second = client.post("/consent")
    assert first.json()["session_id"] == second.json()["session_id"]
