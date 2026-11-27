import os
import sys
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import (
    Cow,
    ActivityRecord,
    DailyActivitySummary,
    ActivityAlert,
    TemperatureRecord,
    HeartRateRecord,
    GPSRecord,
)
from backend.app.services.llm_vet_service import LLMVetService, llm_vet_service
from backend.app.schemas.vet import CowTelemetrySnapshot, SimpleDiagnosticCard

client = TestClient(app)


def test_normal_healthy_cow_simulation():
    """Verify that a normal healthy cow receives a NORMAL triage card."""
    payload = {
        "cow_id": 1,
        "cow_tag": "COW-001",
        "current_activity": "grazing",
        "activity_confidence": 0.98,
        "daily_grazing_hours": 8.5,
        "daily_lying_hours": 9.5,
        "daily_walking_hours": 2.2,
        "active_activity_alerts": [],
        "skin_temperature": 34.0,
        "ambient_temperature": 22.0,
        "corrected_temperature": 38.5,
        "temperature_status": "NORMAL",
        "cusum_fever_score": 0.0,
        "cusum_hypo_score": 0.0,
        "heart_rate_bpm": 64.0,
        "baseline_bpm": 65.0,
        "heart_rate_delta_pct": -1.5,
        "heart_rate_status": "NORMAL",
        "gps_lat": 25.2600,
        "gps_lon": 87.0100,
        "gps_behavior": "Grazing",
        "is_outside_geofence": False,
        "geofence_breach": False,
    }
    response = client.post("/api/v1/vet/diagnose", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["triage_level"] == "NORMAL"
    assert "Healthy" in data["headline"]
    assert len(data["key_indicators"]) >= 2
    assert len(data["action_steps"]) >= 1


def test_acute_mastitis_fever_simulation():
    """Verify that high fever + tachycardia + feeding deficit triggers EMERGENCY triage."""
    payload = {
        "cow_id": 2,
        "cow_tag": "COW-002",
        "current_activity": "lying",
        "activity_confidence": 0.94,
        "daily_grazing_hours": 3.2,
        "daily_lying_hours": 14.0,
        "daily_walking_hours": 1.0,
        "active_activity_alerts": ["FEEDING_DEFICIT"],
        "skin_temperature": 36.5,
        "ambient_temperature": 22.0,
        "corrected_temperature": 39.9,
        "temperature_status": "CRITICAL_FEVER",
        "cusum_fever_score": 2.15,
        "cusum_hypo_score": 0.0,
        "heart_rate_bpm": 88.0,
        "baseline_bpm": 65.0,
        "heart_rate_delta_pct": 35.4,
        "heart_rate_status": "HIGH_HEART_RATE",
        "gps_lat": 25.2605,
        "gps_lon": 87.0102,
        "gps_behavior": "Resting",
        "is_outside_geofence": False,
        "geofence_breach": False,
    }
    response = client.post("/api/v1/vet/diagnose", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["triage_level"] == "EMERGENCY"
    assert "Fever" in data["headline"] or "Mastitis" in data["headline"]
    assert any("udder" in step.lower() or "mastitis" in step.lower() for step in data["action_steps"])


def test_milk_fever_hypocalcemia_simulation():
    """Verify that subnormal temperature + bradycardia triggers EMERGENCY Milk Fever triage."""
    payload = {
        "cow_id": 3,
        "cow_tag": "COW-003",
        "current_activity": "lying",
        "activity_confidence": 0.99,
        "daily_grazing_hours": 1.5,
        "daily_lying_hours": 18.0,
        "daily_walking_hours": 0.4,
        "active_activity_alerts": [],
        "skin_temperature": 32.0,
        "ambient_temperature": 20.0,
        "corrected_temperature": 37.1,
        "temperature_status": "CRITICAL_HYPOTHERMIA",
        "cusum_fever_score": 0.0,
        "cusum_hypo_score": 1.65,
        "heart_rate_bpm": 42.0,
        "baseline_bpm": 65.0,
        "heart_rate_delta_pct": -35.4,
        "heart_rate_status": "LOW_HEART_RATE",
        "gps_lat": 25.2601,
        "gps_lon": 87.0103,
        "gps_behavior": "Resting",
        "is_outside_geofence": False,
        "geofence_breach": False,
    }
    response = client.post("/api/v1/vet/diagnose", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["triage_level"] == "EMERGENCY"
    assert "Milk Fever" in data["headline"] or "Hypothermia" in data["headline"]
    assert any("calcium" in step.lower() for step in data["action_steps"])


def test_estrus_standing_heat_simulation():
    """Verify that behavioral surge in walking triggers ATTENTION Estrus triage."""
    payload = {
        "cow_id": 4,
        "cow_tag": "COW-004",
        "current_activity": "walking",
        "activity_confidence": 0.95,
        "daily_grazing_hours": 7.0,
        "daily_lying_hours": 5.2,
        "daily_walking_hours": 4.8,
        "active_activity_alerts": ["ESTRUS_SUSPECTED"],
        "skin_temperature": 34.2,
        "ambient_temperature": 22.0,
        "corrected_temperature": 38.6,
        "temperature_status": "NORMAL",
        "cusum_fever_score": 0.0,
        "cusum_hypo_score": 0.0,
        "heart_rate_bpm": 68.0,
        "baseline_bpm": 65.0,
        "heart_rate_delta_pct": 4.6,
        "heart_rate_status": "NORMAL",
        "gps_lat": 25.2612,
        "gps_lon": 87.0115,
        "gps_behavior": "Walking",
        "is_outside_geofence": False,
        "geofence_breach": False,
    }
    response = client.post("/api/v1/vet/diagnose", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["triage_level"] == "ATTENTION"
    assert "Heat" in data["headline"] or "Insemination" in data["headline"]
    assert any("insemination" in step.lower() or "ai" in step.lower() for step in data["action_steps"])


def test_geofence_breach_simulation():
    """Verify that pasture breach triggers ATTENTION breach triage."""
    payload = {
        "cow_id": 5,
        "cow_tag": "COW-005",
        "current_activity": "walking",
        "activity_confidence": 0.92,
        "daily_grazing_hours": 8.0,
        "daily_lying_hours": 9.0,
        "daily_walking_hours": 2.5,
        "active_activity_alerts": [],
        "skin_temperature": 34.0,
        "ambient_temperature": 22.0,
        "corrected_temperature": 38.5,
        "temperature_status": "NORMAL",
        "cusum_fever_score": 0.0,
        "cusum_hypo_score": 0.0,
        "heart_rate_bpm": 66.0,
        "baseline_bpm": 65.0,
        "heart_rate_delta_pct": 1.5,
        "heart_rate_status": "NORMAL",
        "gps_lat": 25.2750,
        "gps_lon": 87.0250,
        "gps_behavior": "Walking",
        "is_outside_geofence": True,
        "geofence_breach": True,
    }
    response = client.post("/api/v1/vet/diagnose", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["triage_level"] == "ATTENTION"
    assert "Breach" in data["headline"]
    assert any("coordinates" in step.lower() or "fence" in step.lower() for step in data["action_steps"])


def test_db_retrieval_and_diagnosis_endpoint():
    """Verify GET /api/v1/cows/{cow_id}/vet-diagnosis with actual database entries."""
    db = SessionLocal()
    try:
        # Create test cow if not exists
        cow = db.query(Cow).filter(Cow.tag_id == "VET-TEST-01").first()
        if not cow:
            cow = Cow(tag_id="VET-TEST-01", name="Daisy", breed="Jersey", age_months=36)
            db.add(cow)
            db.commit()
            db.refresh(cow)

        now = datetime.now(timezone.utc)

        # Add records
        db.add(ActivityRecord(cow_id=cow.id, timestamp=now, predicted_behavior="eating", confidence=0.96))
        db.add(TemperatureRecord(
            cow_id=cow.id, timestamp=now, skin_temperature=34.1, ambient_temperature=22.0,
            corrected_temperature=38.6, expected_baseline_temp=38.6, residual_delta=0.0,
            cusum_positive=0.0, cusum_negative=0.0, status="NORMAL"
        ))
        db.add(HeartRateRecord(
            cow_id=cow.id, timestamp=now, heart_rate=65.0, baseline_bpm=65.0,
            delta_bpm=0.0, delta_pct=0.0, status="NORMAL"
        ))
        db.add(GPSRecord(
            cow_id=cow.id, timestamp=now, lat=25.2602, lon=87.0101,
            gps_behavior="Grazing", is_outside=False, geofence_breach=False
        ))
        db.commit()

        # Query endpoint
        response = client.get(f"/api/v1/cows/{cow.id}/vet-diagnosis")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["cow_id"] == cow.id
        assert data["cow_tag"] == "VET-TEST-01"
        assert data["triage_level"] == "NORMAL"
        assert "Healthy" in data["headline"]
    finally:
        db.close()


def test_gemini_api_mock_execution():
    """Verify that LLMVetService invokes Gemini 3.8 Flash model and parses response."""
    service = LLMVetService(model_name="gemini-3.8-flash", api_key="fake-test-key")
    snapshot = CowTelemetrySnapshot(
        cow_id=99,
        cow_tag="COW-099",
        current_activity="walking",
        corrected_temperature=38.7,
        heart_rate_bpm=66.0,
        gps_lat=25.2600,
        gps_lon=87.0100,
    )

    fake_gemini_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": """{
                                "cow_id": 99,
                                "cow_tag": "COW-099",
                                "triage_level": "NORMAL",
                                "headline": "Optimal Herd Vitality",
                                "farmer_message": "Cow COW-099 is in excellent physical condition with steady circadian thermoregulation and strong baseline pacing.",
                                "key_indicators": ["Normal body temperature at 38.7°C", "Stable resting pulse of 66 BPM", "Safe inside pasture bounds"],
                                "action_steps": ["Maintain current grazing rotation", "Inspect water trough clarity"]
                            }"""
                        }
                    ]
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fake_gemini_response

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        card = service.diagnose(snapshot)
        assert card.triage_level == "NORMAL"
        assert card.headline == "Optimal Herd Vitality"
        assert "COW-099" in card.farmer_message
        assert len(card.key_indicators) == 3
        assert len(card.action_steps) == 2
        # Verify URL uses gemini-3.8-flash
        called_url = mock_post.call_args[0][0]
        assert "gemini-3.8-flash" in called_url


if __name__ == "__main__":
    print("Running LLM Vet unit and integration tests...")
    test_normal_healthy_cow_simulation()
    print(" [PASS] test_normal_healthy_cow_simulation")
    test_acute_mastitis_fever_simulation()
    print(" [PASS] test_acute_mastitis_fever_simulation")
    test_milk_fever_hypocalcemia_simulation()
    print(" [PASS] test_milk_fever_hypocalcemia_simulation")
    test_estrus_standing_heat_simulation()
    print(" [PASS] test_estrus_standing_heat_simulation")
    test_geofence_breach_simulation()
    print(" [PASS] test_geofence_breach_simulation")
    test_db_retrieval_and_diagnosis_endpoint()
    print(" [PASS] test_db_retrieval_and_diagnosis_endpoint")
    test_gemini_api_mock_execution()
    print(" [PASS] test_gemini_api_mock_execution")
    print("All LLM Vet tests passed successfully!")
