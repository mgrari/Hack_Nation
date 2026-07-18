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
