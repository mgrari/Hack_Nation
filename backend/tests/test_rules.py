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
    db.add(FieldRecord(document_id=doc.id, field_name="pay_frequency", confirmed_value="monthly", confirmed=True))
    db.commit()

    response = client.post("/calculate", json={"household_size": 4, "ami_tier": "60"})
    assert response.status_code == 200
    body = response.json()
    assert body["threshold"] == 102840
    assert body["confirmed_value"] == 90000  # annualize(7500, "monthly")
    assert body["threshold_comparison"] == "below_or_equal"
    assert "eligible" not in str(body).lower()


def test_calculate_returns_readiness_status_and_review_reasons(client):
    from db import get_db
    from main import app
    from models import DocumentRecord, FieldRecord

    client.post("/consent")
    session_id = client.cookies.get("realdoor_session")

    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    pay_stub = DocumentRecord(
        session_id=session_id,
        encrypted_path="unused",
        content_type="application/pdf",
        document_type="pay_stub",
    )
    summary = DocumentRecord(
        session_id=session_id,
        encrypted_path="unused",
        content_type="application/pdf",
        document_type="application_summary",
    )
    db.add_all([pay_stub, summary])
    db.commit()
    db.add(FieldRecord(document_id=pay_stub.id, field_name="gross_pay", confirmed_value="7500", confirmed=True, source_box=[0, 0, 1, 1]))
    db.add(FieldRecord(document_id=pay_stub.id, field_name="pay_frequency", confirmed_value="monthly", confirmed=True, source_box=[0, 0, 1, 1]))
    db.add(FieldRecord(document_id=summary.id, field_name="household_size", confirmed_value="4", confirmed=True, source_box=[0, 0, 1, 1]))
    db.commit()

    response = client.post("/calculate", json={"household_size": 4, "ami_tier": "60"})
    assert response.status_code == 200
    body = response.json()

    # Only application_summary and employment_letter are missing here -- pay_stub's
    # presence corroborates income without employment_letter, so this stays ready.
    assert body["readiness_status"] == "READY_TO_REVIEW"
    assert body["review_reasons"] == []
    assert "eligible" not in str(body).lower()


def test_calculate_returns_above_threshold_comparison(client):
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
    db.add(FieldRecord(document_id=doc.id, field_name="gross_pay", confirmed_value="20000", confirmed=True))
    db.add(FieldRecord(document_id=doc.id, field_name="pay_frequency", confirmed_value="monthly", confirmed=True))
    db.commit()

    response = client.post("/calculate", json={"household_size": 4, "ami_tier": "60"})
    assert response.status_code == 200
    body = response.json()
    assert body["confirmed_value"] == 240000
    assert body["threshold_comparison"] == "above"


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
    db.add(FieldRecord(document_id=doc.id, field_name="pay_frequency", confirmed_value="monthly", confirmed=True))
    db.commit()

    response = client.post("/calculate", json={"household_size": 4, "ami_tier": "60"})
    assert response.status_code == 400
    assert "gross_pay" in response.json()["detail"]


def test_calculate_rejects_missing_pay_frequency(client):
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
    assert response.status_code == 400
    assert "pay_frequency" in response.json()["detail"]


def test_ask_answers_from_ingested_corpus(client, monkeypatch, tmp_path):
    import rules_rag

    monkeypatch.setattr(rules_rag, "CHROMA_DIR", tmp_path / "chroma")
    rules_rag.ingest_corpus()

    class FakeChoice:
        def __init__(self, content):
            self.message = type("Msg", (), {"content": content})()

    class FakeResponse:
        def __init__(self, content):
            self.choices = [FakeChoice(content)]

    def fake_create(**kwargs):
        return FakeResponse("For a household of 4, the 60% AMI limit is $102,840. Source: HUD MTSP FY2026, effective 2026-04-01.")

    monkeypatch.setattr("routers.rules.OpenAI", lambda api_key: type(
        "Client", (), {"chat": type("Chat", (), {"completions": type("Completions", (), {"create": staticmethod(fake_create)})()})()}
    )())

    client.post("/consent")
    response = client.post("/ask", json={"question": "What's the income limit for a household of 4?"})
    assert response.status_code == 200
    body = response.json()
    assert "102,840" in body["answer"] or "102840" in body["answer"]
    assert len(body["citations"]) > 0


def test_ask_refuses_to_state_eligibility_verdict(client, monkeypatch, tmp_path):
    import rules_rag
    from routers.rules import ASK_SYSTEM_PROMPT

    monkeypatch.setattr(rules_rag, "CHROMA_DIR", tmp_path / "chroma")
    rules_rag.ingest_corpus()

    # The system prompt itself must instruct the model never to state a verdict.
    prompt = ASK_SYSTEM_PROMPT.lower()
    assert "never state or imply whether a specific renter is eligible" in prompt

    class FakeChoice:
        def __init__(self, content):
            self.message = type("Msg", (), {"content": content})()

    class FakeResponse:
        def __init__(self, content):
            self.choices = [FakeChoice(content)]

    captured_messages = {}

    def fake_create(**kwargs):
        captured_messages["messages"] = kwargs["messages"]
        # Even under a direct request for a verdict, a compliant model sticks to the rule's
        # numbers and citation rather than answering "yes"/"no".
        return FakeResponse(
            "I don't have enough information to say whether you personally qualify. "
            "For a household of 4, the 60% AMI limit is $102,840. "
            "Source: HUD MTSP FY2026, effective 2026-04-01."
        )

    monkeypatch.setattr("routers.rules.OpenAI", lambda api_key: type(
        "Client", (), {"chat": type("Chat", (), {"completions": type("Completions", (), {"create": staticmethod(fake_create)})()})()}
    )())

    client.post("/consent")
    response = client.post("/ask", json={"question": "Just tell me if I'm eligible for this program"})
    assert response.status_code == 200
    body = response.json()

    # Response schema can never carry a verdict field -- only answer + citations.
    assert set(body.keys()) == {"answer", "citations"}

    answer_lower = body["answer"].lower()
    assert "you're eligible" not in answer_lower
    assert "you are eligible" not in answer_lower
    assert "you're approved" not in answer_lower
    assert "you are approved" not in answer_lower

    # The system prompt with the refusal instruction was actually sent to the model.
    sent_system_message = captured_messages["messages"][0]["content"]
    assert sent_system_message == ASK_SYSTEM_PROMPT
