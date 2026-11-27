import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base, SessionLocal
from app.models import Cow, HeartRateRecord, HeartRateAlert
from app.services.heart_rate_service import HeartRateService

client = TestClient(app)

def run_heart_rate_tests():
    print("=" * 70)
    print("STARTING HEART RATE SERVICE INTEGRATION TEST SUITE")
    print("=" * 70)

    # 1. Health check & Root endpoint
    print("\n--- 1. Testing System Health & Endpoints ---")
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "heart_rate_telemetry" in data["endpoints"]
    assert "heart_rate_alerts" in data["endpoints"]
    print(f"[PASS] System status: {data['status']}, Heart Rate endpoints registered.")

    # 2. Cow registration & cleanup
    print("\n--- 2. Registering Test Cows & Clearing Previous Test Runs ---")
    tag_id_high = "COW_HR_01"
    tag_id_low = "COW_HR_02"
    tag_id_batch = "COW_HR_03"

    db = SessionLocal()
    for tid in [tag_id_high, tag_id_low, tag_id_batch]:
        c = db.query(Cow).filter(Cow.tag_id == tid).first()
        if c:
            db.query(HeartRateRecord).filter(HeartRateRecord.cow_id == c.id).delete()
            db.query(HeartRateAlert).filter(HeartRateAlert.cow_id == c.id).delete()
    db.commit()
    db.close()

    client.post("/api/v1/cows/", json={"tag_id": tag_id_high, "name": "Bella - High HR Test", "breed": "Jersey"})
    client.post("/api/v1/cows/", json={"tag_id": tag_id_low, "name": "Luna - Low HR Test", "breed": "Holstein"})
    client.post("/api/v1/cows/", json={"tag_id": tag_id_batch, "name": "Stella - Batch Test", "breed": "Angus"})
    print(f"[PASS] Registered test cows.")

    # 3. Normal Heart Rate Ingestion
    print("\n--- 3. Testing Normal Heart Rate Stream (Healthy Baseline) ---")
    now = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    res = client.post("/api/v1/heart-rate/telemetry", json={
        "tag_id": tag_id_high,
        "timestamp": now.isoformat(),
        "heart_rate": 64.0
    })
    assert res.status_code == 201
    normal_data = res.json()
    assert normal_data["status"] == "NORMAL"
    assert normal_data["alert_triggered"] is False
    assert normal_data["baseline_bpm"] == 65.0
    print(f"[PASS] Ingested 64 BPM: Status is {normal_data['status']}, Delta: {normal_data['delta_pct']}%.")

    # 4. Rule 1: High Heart Rate / Tachycardia
    print("\n--- 4. Testing Rule 1: High Heart Rate (Pain / Acute Stress) ---")
    t_high = now + timedelta(minutes=15)
    res_high = client.post("/api/v1/heart-rate/telemetry", json={
        "tag_id": tag_id_high,
        "timestamp": t_high.isoformat(),
        "heart_rate": 92.0
    })
    assert res_high.status_code == 201
    high_data = res_high.json()
    print(f"  BPM: {high_data['heart_rate']} | Baseline: {high_data['baseline_bpm']} | Delta: {high_data['delta_pct']:+}% | Status: {high_data['status']}")
    assert high_data["status"] == "HIGH_HEART_RATE"
    assert high_data["alert_triggered"] is True
    assert high_data["delta_pct"] >= 30.0

    # Verify Alert in DB
    alerts_res = client.get(f"/api/v1/heart-rate/cow/{tag_id_high}/alerts")
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) >= 1
    assert alerts[0]["alert_type"] == "HIGH_HEART_RATE"
    print(f"[PASS] High Heart Rate correctly flagged: {alerts[0]['clinical_notes']}")

    # 5. Rule 2: Low Heart Rate / Bradycardia
    print("\n--- 5. Testing Rule 2: Low Heart Rate (Milk Fever / Lethargy) ---")
    res_low = client.post("/api/v1/heart-rate/telemetry", json={
        "tag_id": tag_id_low,
        "timestamp": now.isoformat(),
        "heart_rate": 42.0
    })
    assert res_low.status_code == 201
    low_data = res_low.json()
    print(f"  BPM: {low_data['heart_rate']} | Baseline: {low_data['baseline_bpm']} | Delta: {low_data['delta_pct']:+}% | Status: {low_data['status']}")
    assert low_data["status"] == "LOW_HEART_RATE"
    assert low_data["alert_triggered"] is True
    assert low_data["delta_pct"] <= -25.0

    low_alerts = client.get(f"/api/v1/heart-rate/cow/{tag_id_low}/alerts").json()
    assert len(low_alerts) >= 1
    assert low_alerts[0]["alert_type"] == "LOW_HEART_RATE"
    print(f"[PASS] Low Heart Rate correctly flagged: {low_alerts[0]['clinical_notes']}")

    # 6. Batch Telemetry & Baseline Learning
    print("\n--- 6. Testing Batch Telemetry & Personalized Baseline Learning ---")
    batch_readings = []
    base_t = datetime.now(timezone.utc) - timedelta(days=1)
    # Seed 6 readings around 60 BPM
    for i in range(6):
        batch_readings.append({
            "timestamp": (base_t + timedelta(hours=i)).isoformat(),
            "heart_rate": 60.0
        })

    batch_resp = client.post("/api/v1/heart-rate/telemetry/batch", json={
        "tag_id": tag_id_batch,
        "readings": batch_readings
    })
    assert batch_resp.status_code == 201
    assert batch_resp.json()["total_processed"] == 6
    assert batch_resp.json()["alerts_triggered"] == 0

    # Query learned baseline
    base_resp = client.get(f"/api/v1/heart-rate/cow/{tag_id_batch}/baseline")
    assert base_resp.status_code == 200
    base_info = base_resp.json()
    assert base_info["is_custom_baseline"] is True
    assert abs(base_info["baseline_bpm"] - 60.0) < 0.5
    print(f"[PASS] Learned personalized baseline: {base_info['baseline_bpm']} BPM across {base_info['sample_count']} samples.")

    # 7. Alert Acknowledgment
    print("\n--- 7. Testing Alert Acknowledgment ---")
    alert_id = alerts[0]["id"]
    ack_res = client.post(f"/api/v1/heart-rate/alerts/{alert_id}/acknowledge")
    assert ack_res.status_code == 200
    assert ack_res.json()["acknowledged"] is True
    print(f"[PASS] Alert ID {alert_id} successfully acknowledged.")

    print("\n" + "=" * 70)
    print("ALL HEART RATE TESTS PASSED SUCCESSFULLY! ZERO ERRORS.")
    print("=" * 70)

if __name__ == "__main__":
    run_heart_rate_tests()
