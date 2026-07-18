from datetime import datetime, timedelta


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
