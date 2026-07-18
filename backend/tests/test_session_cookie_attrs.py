def test_cookie_is_lax_and_insecure_in_development(client):
    response = client.post("/consent")
    set_cookie = response.headers["set-cookie"]
    assert "samesite=lax" in set_cookie.lower()
    assert "secure" not in set_cookie.lower()


def test_cookie_is_none_and_secure_in_production(client, monkeypatch):
    from config import settings

    monkeypatch.setattr(settings, "environment", "production")
    response = client.post("/consent")
    set_cookie = response.headers["set-cookie"]
    assert "samesite=none" in set_cookie.lower()
    assert "secure" in set_cookie.lower()
