import json
from datetime import datetime, timedelta
from pathlib import Path

CHECKLIST_PATH = Path(__file__).parent.parent / "data" / "checklists" / "gold_checklist.json"


def load_gold_checklist() -> list[dict]:
    try:
        with open(CHECKLIST_PATH) as f:
            return json.load(f)["items"]
    except FileNotFoundError:
        raise FileNotFoundError(f"Gold checklist file not found: {CHECKLIST_PATH}.")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Gold checklist file is not valid JSON: {CHECKLIST_PATH} ({e.msg})", e.doc, e.pos
        )


def evaluate_checklist(confirmed_fields: dict, consent_given: bool) -> list[dict]:
    items = load_gold_checklist()
    results = []
    for item in items:
        if item["id"] == "consent_form":
            status = "present" if consent_given else "missing"
        elif item["requires_field"]:
            value = confirmed_fields.get(item["requires_field"])
            if not value:
                status = "missing"
            elif item["max_age_days"]:
                try:
                    field_date = datetime.fromisoformat(value)
                except ValueError:
                    status = "missing"
                else:
                    age = datetime.utcnow() - field_date
                    status = "expired" if age > timedelta(days=item["max_age_days"]) else "present"
            else:
                status = "present"
        else:
            # Not extractable from a pay stub in v1 (photo ID, household proof, SSN/ITIN) —
            # always reported missing until a future doc type covers it.
            status = "missing"
        results.append({"id": item["id"], "label": item["label"], "status": status})
    return results
