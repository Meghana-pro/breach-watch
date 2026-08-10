import os
import tempfile
from pathlib import Path

# Use a separate database for tests.
TEST_DB = Path(tempfile.gettempdir()) / "breach_watch_test.db"
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["BREACH_WATCH_DB_PATH"] = str(TEST_DB)

from fastapi.testclient import TestClient
from app.main import app
from app.risk import score_incident

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert "BreachWatch" in response.text


def test_seeded_incidents_exist():
    response = client.get("/api/incidents")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_sensitive_categories_raise_score():
    low = score_incident(["usernames"])
    high = score_incident(["passwords", "authentication_tokens", "financial_data"])
    assert high["risk_score"] > low["risk_score"]
    assert high["risk_level"] in {"Medium", "High"}


def test_create_and_complete_action():
    payload = {
        "organization": "Test Organization",
        "title": "Test incident report",
        "description": "Fictional test record for automated tests.",
        "source_name": "Pytest",
        "source_url": "",
        "incident_date": "2026-01-15",
        "data_types": ["email_addresses"]
    }
    created = client.post("/api/incidents", json=payload)
    assert created.status_code == 201
    incident_id = created.json()["id"]
    assert created.json()["risk_level"] in {"Low", "Medium", "High"}

    updated = client.patch(f"/api/incidents/{incident_id}/action", json={"completed": True})
    assert updated.status_code == 200
    assert updated.json()["action_completed"] is True


def test_missing_incident_action_returns_404():
    response = client.patch("/api/incidents/999999/action", json={"completed": True})
    assert response.status_code == 404
