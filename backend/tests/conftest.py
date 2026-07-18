import pytest
from cryptography.fernet import Fernet


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from db import Base, get_db
    import models  # noqa: F401  ensures all tables are registered on Base.metadata
    from main import app

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    from fastapi.testclient import TestClient

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    test_client.session_local = testing_session_local
    yield test_client
    app.dependency_overrides.clear()
