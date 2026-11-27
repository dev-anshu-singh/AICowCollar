import os
import sys
import math
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add backend directory to sys.path so app modules import cleanly
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base, SessionLocal
from app.models import Cow, TemperatureRecord, TemperatureBaseline, TemperatureAlert
from app.services.temperature_service import TemperatureAnomalyService

client = TestClient(app)

def run_temperature_tests():
    print("=" * 70)
    print("STARTING TEMPERATURE SERVICE & CUSUM INTEGRATION TEST SUITE")
    print("=" * 70)

    # 1. Health check & Root endpoint
    print("\n--- 1. Testing System Health & Endpoints ---")
    response = client.get("/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "temperature_telemetry" in data["endpoints"]
    print(f"[PASS] System status: {data['status']}, Temperature endpoints registered.")

    # 2. Cow registration & cleanup
    print("\n--- 2. Registering Test Cows & Clearing Previous Test Runs ---")
    tag_id_fever = "COW_TEMP_01"
    tag_id_hypo = "COW_TEMP_02"
    tag_id_batch = "COW_TEMP_03"

    db = SessionLocal()
    for tid in [tag_id_fever, tag_id_hypo, tag_id_batch]:
        c = db.query(Cow).filter(Cow.tag_id == tid).first()
        if c:
            db.query(TemperatureRecord).filter(TemperatureRecord.cow_id == c.id).delete()
            db.query(TemperatureAlert).filter(TemperatureAlert.cow_id == c.id).delete()
            db.query(TemperatureBaseline).filter(TemperatureBaseline.cow_id == c.id).delete()
    db.commit()
    db.close()

    client.post("/api/v1/cows/", json={"tag_id": tag_id_fever, "name": "Bessie - Fever Test", "breed": "Jersey"})
    client.post("/api/v1/cows/", json={"tag_id": tag_id_hypo, "name": "Daisy - Milk Fever Test", "breed": "Holstein"})
    print(f"[PASS] Registered & cleared test data for {tag_id_fever} and {tag_id_hypo}.")

    # 3. Ambient Decoupling Verification
    print("\n--- 3. Testing Ambient Temperature Decoupling ---")
    # T_skin = 39.5, T_ambient = 35.0 (hot sunny afternoon).
    # Expected corrected = 39.5 - 0.12 * (35 - 22) = 39.5 - 1.56 = 37.94°C
    corrected = TemperatureAnomalyService.decouple_ambient_temperature(39.5, 35.0)
    assert abs(corrected - 37.94) < 0.05, f"Expected 37.94, got {corrected}"
    print(f"[PASS] Ambient Decoupling: Raw Skin 39.5°C at 35°C ambient -> Corrected to {corrected}°C.")

    # 4. Circadian Rhythm Diurnal Baseline
    print("\n--- 4. Testing Bovine Circadian Rhythm Model ---")
    trough_mean, _ = TemperatureAnomalyService.get_default_circadian_temp(4)   # 04:00 AM (trough)
    peak_mean, _ = TemperatureAnomalyService.get_default_circadian_temp(16)   # 04:00 PM (peak)
    assert trough_mean < peak_mean, f"Trough {trough_mean} should be lower than peak {peak_mean}"
    assert 38.0 <= trough_mean <= 38.2, f"Expected trough around 38.1°C, got {trough_mean}"
    assert 38.8 <= peak_mean <= 39.0, f"Expected peak around 38.9°C, got {peak_mean}"
    print(f"[PASS] Circadian diurnal curve: 04:00 AM (Trough: {trough_mean}°C) vs 16:00 PM (Peak: {peak_mean}°C).")

    # 5. Normal Telemetry Ingestion (No CUSUM Alert)
    print("\n--- 5. Testing Normal Telemetry Stream (Healthy Cow) ---")
    now = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
    for i in range(4):
        t = now + timedelta(minutes=15 * i)
        # Normal reading at 10 AM ~ 38.5°C
        res = client.post("/api/v1/temperature/telemetry", json={
            "tag_id": tag_id_fever,
            "timestamp": t.isoformat(),
            "skin_temperature": 38.5,
            "ambient_temperature": 22.0
        })
        assert res.status_code == 201
        res_data = res.json()
        assert res_data["status"] == "NORMAL"
        assert res_data["cusum_positive"] == 0.0
        assert res_data["alert_triggered"] is False

    print("[PASS] 4 consecutive normal readings ingested. CUSUM remains at 0.0 with status NORMAL.")

    # 6. Scenario A: Mastitis / BRD Fever Onset (Upper CUSUM Accumulation)
    print("\n--- 6. Testing Scenario A: Early Fever Inception via CUSUM ---")
    # Simulate acute bacterial infection: temperature steadily climbs above circadian expectation
    fever_readings = [
        # (hour_offset, skin_temp, expected_status)
        (1.0, 39.2, "NORMAL"),             # delta = +0.6, slack = 0.3 -> s+ = 0.30 (<1.20 warning)
        (1.5, 39.8, "SUSPECTED_FEVER"),    # delta = +1.2, slack = 0.3 -> s+ = 0.30 + 0.90 = 1.20 (>=1.20 WARNING)
        (2.0, 40.2, "SUSPECTED_FEVER"),    # delta = +1.6, slack = 0.3 -> s+ = 1.20 + 1.30 = 2.50 (>=2.00 CRITICAL)
    ]

    latest_fever_record = None
    for offset_h, temp, expected_st in fever_readings:
        t = now + timedelta(hours=offset_h)
        res = client.post("/api/v1/temperature/telemetry", json={
            "tag_id": tag_id_fever,
            "timestamp": t.isoformat(),
            "skin_temperature": temp,
            "ambient_temperature": 22.0
        })
        assert res.status_code == 201
        data = res.json()
        print(f"  Hour +{offset_h}h | Temp: {temp}°C | Delta: {data['residual_delta']:+.2f}°C | CUSUM S+: {data['cusum_positive']} | Status: {data['status']}")
        assert data["status"] == expected_st, f"Expected {expected_st}, got {data['status']}"
        latest_fever_record = data

    assert latest_fever_record["status"] == "SUSPECTED_FEVER"
    assert latest_fever_record["cusum_positive"] >= 2.0
    print("[PASS] Upper CUSUM accumulated and correctly triggered SUSPECTED_FEVER (CRITICAL)!")

    # Check that alert was persisted
    alert_res = client.get(f"/api/v1/temperature/cow/{tag_id_fever}/alerts")
    assert alert_res.status_code == 200
    alerts = alert_res.json()
    assert len(alerts) >= 1
    fever_alert = alerts[0]
    assert fever_alert["alert_type"] == "SUSPECTED_FEVER"
    assert fever_alert["severity"] in ["WARNING", "CRITICAL"]
    print(f"[PASS] Persisted Alert: {fever_alert['alert_type']} ({fever_alert['severity']}) - {fever_alert['clinical_notes']}")

    # 7. Scenario B: Milk Fever / Hypothermia (Lower CUSUM Accumulation)
    print("\n--- 7. Testing Scenario B: Milk Fever Hypothermia via CUSUM ---")
    hypo_time = datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc)
    hypo_readings = [
        # Expected baseline at 14:00 is ~38.85°C.
        (0.5, 37.8, "NORMAL"),                # delta = -1.05, lower dev = 1.05 - 0.3 = 0.75
        (1.0, 37.2, "SUSPECTED_HYPOTHERMIA"), # delta = -1.65, lower dev = 1.35 -> s- = 2.10
        (1.5, 36.8, "SUSPECTED_HYPOTHERMIA"), # delta = -2.05, lower dev = 1.75 -> s- = 3.85
    ]

    for offset_h, temp, expected_st in hypo_readings:
        t = hypo_time + timedelta(hours=offset_h)
        res = client.post("/api/v1/temperature/telemetry", json={
            "tag_id": tag_id_hypo,
            "timestamp": t.isoformat(),
            "skin_temperature": temp,
            "ambient_temperature": 22.0
        })
        assert res.status_code == 201
        data = res.json()
        print(f"  Hour +{offset_h}h | Temp: {temp}°C | Delta: {data['residual_delta']:+.2f}°C | CUSUM S-: {data['cusum_negative']} | Status: {data['status']}")
        assert data["status"] == expected_st

    hypo_alert_res = client.get(f"/api/v1/temperature/cow/{tag_id_hypo}/alerts")
    hypo_alerts = hypo_alert_res.json()
    assert len(hypo_alerts) >= 1
    assert hypo_alerts[0]["alert_type"] == "SUSPECTED_HYPOTHERMIA"
    print(f"[PASS] Lower CUSUM accumulated and correctly triggered {hypo_alerts[0]['alert_type']} ({hypo_alerts[0]['severity']})!")

    # 8. Batch Ingestion Test
    print("\n--- 8. Testing Batch Telemetry Upload ---")
    tag_id_batch = "COW_TEMP_03"
    client.post("/api/v1/cows/", json={"tag_id": tag_id_batch, "name": "Buttercup", "breed": "Angus"})

    batch_readings = []
    base_ts = datetime(2026, 6, 2, 0, 0, tzinfo=timezone.utc)
    for hour in range(24):
        mean_t, _ = TemperatureAnomalyService.get_default_circadian_temp(hour)
        amb_t = 20.0 + 5.0 * math.sin(2 * math.pi * (hour - 8) / 24)
        # Raw skin temperature incorporates ambient thermal shift; decoupling will restore mean_t
        raw_skin = round(mean_t + TemperatureAnomalyService.BETA_AMBIENT * (amb_t - 22.0), 2)
        batch_readings.append({
            "timestamp": (base_ts + timedelta(hours=hour)).isoformat(),
            "skin_temperature": raw_skin,
            "ambient_temperature": round(amb_t, 2)
        })

    batch_res = client.post("/api/v1/temperature/telemetry/batch", json={
        "tag_id": tag_id_batch,
        "readings": batch_readings
    })
    assert batch_res.status_code == 201
    batch_data = batch_res.json()
    assert batch_data["total_processed"] == 24
    assert batch_data["alerts_triggered"] == 0
    print(f"[PASS] Ingested 24-hour batch stream. Processed {batch_data['total_processed']} readings smoothly.")

    # 9. Diurnal Baseline Recomputation & Query
    print("\n--- 9. Testing Diurnal Baseline Learning & Profile Retrieval ---")
    recompute_res = client.post(f"/api/v1/temperature/cow/{tag_id_batch}/recompute-baseline?days=7")
    assert recompute_res.status_code == 200
    baseline_profile = recompute_res.json()
    assert len(baseline_profile["diurnal_profile"]) == 24
    print(f"[PASS] 24-hour diurnal profile retrieved. Hour 16 Peak: {baseline_profile['diurnal_profile'][16]['mean_temperature']}°C.")

    # 10. Alert Acknowledgment
    print("\n--- 10. Testing Alert Acknowledgment ---")
    alert_to_ack = fever_alert["id"]
    ack_res = client.post(f"/api/v1/temperature/alerts/{alert_to_ack}/acknowledge")
    assert ack_res.status_code == 200
    assert ack_res.json()["acknowledged"] is True
    print(f"[PASS] Alert ID {alert_to_ack} successfully acknowledged by veterinarian/operator.")

    print("\n" + "=" * 70)
    print("ALL TEMPERATURE & CUSUM TESTS PASSED SUCCESSFULLY! ZERO ERRORS.")
    print("=" * 70)

if __name__ == "__main__":
    run_temperature_tests()
