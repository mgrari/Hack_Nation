def test_cors_allows_configured_frontend_origin(client):
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_rejects_unlisted_origin(client):
    response = client.get(
        "/health",
        headers={"Origin": "https://evil.example.com"},
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
