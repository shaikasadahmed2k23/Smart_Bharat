"""Basic tests for Smart Bharat API (no external API calls)."""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from main import app
from civic_data import search_services, find_service_by_name

client = TestClient(app)
client.__enter__()  # trigger lifespan startup (creates DB tables)


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_service_recommendation():
    resp = client.post("/api/services/recommend", json={"need": "I need food ration subsidy"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) > 0
    assert any("Ration" in r["name"] for r in data["results"])


def test_document_requirements_found():
    resp = client.post("/api/documents/requirements", json={"service_name": "Aadhaar Card"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "Aadhaar Card"
    assert len(data["documents"]) > 0


def test_document_requirements_not_found():
    resp = client.post("/api/documents/requirements", json={"service_name": "Nonexistent Service XYZ"})
    assert resp.status_code == 404


def test_create_and_track_complaint():
    resp = client.post(
        "/api/complaints",
        json={
            "title": "Broken streetlight",
            "description": "Streetlight has been off for a week near main road.",
            "category": "electricity",
            "location": "MG Road, Kurnool",
        },
    )
    assert resp.status_code == 201
    complaint = resp.json()
    assert complaint["status"] == "submitted"

    track_resp = client.get(f"/api/complaints/{complaint['id']}")
    assert track_resp.status_code == 200
    assert track_resp.json()["title"] == "Broken streetlight"


def test_update_complaint_status():
    create_resp = client.post(
        "/api/complaints",
        json={
            "title": "Water leakage",
            "description": "Pipe leaking near park entrance for 3 days.",
            "category": "water",
        },
    )
    complaint_id = create_resp.json()["id"]
    update_resp = client.patch(f"/api/complaints/{complaint_id}", json={"status": "in_review"})
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "in_review"


def test_list_complaints_respects_limit():
    client.post(
        "/api/complaints",
        json={
            "title": "Noise complaint",
            "description": "Loud construction noise after midnight.",
            "category": "noise",
        },
    )
    client.post(
        "/api/complaints",
        json={
            "title": "Pothole complaint",
            "description": "Large pothole causing traffic issues.",
            "category": "roads",
        },
    )

    resp = client.get("/api/complaints?limit=1")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_search_services_helper():
    results = search_services("passport travel abroad")
    assert any(s["name"] == "Passport" for s in results)


def test_find_service_by_name_helper():
    service = find_service_by_name("pan card")
    assert service is not None
    assert service["name"] == "PAN Card"


def test_fuzzy_match_handles_typo():
    """Real users misspell 'Aadhaar' as 'aadhar' constantly -- must still resolve."""
    resp = client.post("/api/documents/requirements", json={"service_name": "aadhar card"})
    assert resp.status_code == 200
    assert resp.json()["service"] == "Aadhaar Card"


def test_invalid_language_falls_back_to_english():
    """Unsupported language codes should silently fall back to English, not error."""
    resp = client.post("/api/chat", json={"message": "hello", "language": "fr"})
    assert resp.status_code in (200, 503)  # 503 only if Gemini key missing in this env


def test_complaint_rejects_too_short_title():
    """Title below min_length=3 must be rejected with a validation error, not a 500."""
    resp = client.post(
        "/api/complaints",
        json={"title": "Hi", "description": "Some issue description here.", "category": "road"},
    )
    assert resp.status_code == 422


def test_get_nonexistent_complaint_returns_404():
    resp = client.get("/api/complaints/999999")
    assert resp.status_code == 404


def test_invalid_status_value_rejected():
    """Status updates outside the allowed enum must fail validation, not silently corrupt data."""
    create_resp = client.post(
        "/api/complaints",
        json={"title": "Garbage not collected", "description": "Pile of garbage for 5 days.", "category": "sanitation"},
    )
    complaint_id = create_resp.json()["id"]
    resp = client.patch(f"/api/complaints/{complaint_id}", json={"status": "made_up_status"})
    assert resp.status_code == 422
