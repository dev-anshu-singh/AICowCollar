import os
import sys
from datetime import datetime, date, timedelta, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, Base, engine
from app.models import Cow, ActivityRecord, DailyActivitySummary, ActivityAlert

client = TestClient(app)

def test_full_pipeline():
    print("=" * 70)
    print("1. Testing System Health & Root Endpoint")
    print("=" * 70)
    resp = client.get("/")
    assert resp.status_code == 200, f"Root endpoint failed: {resp.text}"
    print("[PASS] System Status:", resp.json()["status"])

    print("\n" + "=" * 70)
    print("2. Testing Cow Registration")
    print("=" * 70)
    cow_payload = {
        "tag_id": "COW_01",
        "name": "Bessie",
        "breed": "Holstein-Friesian",
        "age_months": 36,
        "lactation_stage": "Mid-Lactation"
    }
    resp = client.post("/api/v1/cows/", json=cow_payload)
    if resp.status_code == 201:
        print("[PASS] Registered cow COW_01 successfully.")
    elif resp.status_code == 400:
        print("[INFO] Cow COW_01 was already registered.")
    else:
        assert False, f"Cow registration failed: {resp.text}"

    resp = client.get("/api/v1/cows/")
    assert resp.status_code == 200
    print(f"[PASS] Total registered cows: {len(resp.json())}")

    print("\n" + "=" * 70)
    print("3. Testing Telemetry Ingestion with Pre-Calculated 12 Features")
    print("=" * 70)
    # 12 features representing an eating cow (head down, high gyroY pitch)
    sample_12_features = {
        "Mean_accX": -0.35,
        "Min_accX": -0.85,
        "Mean_accY": -0.12,
        "RMS_accY": 0.15,
        "Mean_accZ": -0.05,
        "Mean_SVM_gyro": 38.5,
        "Min_SVM_gyro": 14.2,
        "Max_SVM_gyro": 72.0,
        "IQR_gyroY": 18.5,
        "IQR_gyroZ": 12.0,
        "Mean_SVM_acc": 0.42,
        "Sd_SVM_acc": 0.18
    }
    telemetry_payload = {
        "tag_id": "COW_01",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": sample_12_features
    }
    resp = client.post("/api/v1/activity/telemetry", json=telemetry_payload)
    assert resp.status_code == 201, f"Telemetry failed: {resp.text}"
    rec = resp.json()
    print(f"[PASS] Telemetry classified as: {rec['predicted_behavior'].upper()} (Confidence: {rec['confidence']*100:.1f}%)")

    print("\n" + "=" * 70)
    print("4. Testing Telemetry Ingestion with Raw 6x 10-Second Sensor Buffer")
    print("=" * 70)
    # 6 readings of a lying cow (accX > 0, gyro low ~5 deg/s)
    raw_buffer_lying = [
        {"accX": 0.28, "accY": -0.06, "accZ": 0.02, "gyroX": 0.5, "gyroY": -1.2, "gyroZ": 0.8},
        {"accX": 0.30, "accY": -0.05, "accZ": 0.01, "gyroX": 0.4, "gyroY": -1.5, "gyroZ": 0.7},
        {"accX": 0.29, "accY": -0.06, "accZ": 0.02, "gyroX": 0.6, "gyroY": -1.0, "gyroZ": 0.9},
        {"accX": 0.31, "accY": -0.07, "accZ": 0.01, "gyroX": 0.3, "gyroY": -1.8, "gyroZ": 0.6},
        {"accX": 0.27, "accY": -0.06, "accZ": 0.03, "gyroX": 0.5, "gyroY": -1.4, "gyroZ": 0.8},
        {"accX": 0.29, "accY": -0.05, "accZ": 0.02, "gyroX": 0.4, "gyroY": -1.1, "gyroZ": 0.7}
    ]
    raw_payload = {
        "tag_id": "COW_01",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "raw_buffer": raw_buffer_lying
    }
    resp = client.post("/api/v1/activity/telemetry", json=raw_payload)
    assert resp.status_code == 201, f"Raw buffer failed: {resp.text}"
    rec = resp.json()
    print(f"[PASS] Raw Buffer classified on-the-fly as: {rec['predicted_behavior'].upper()} (Confidence: {rec['confidence']*100:.1f}%)")

    print("\n" + "=" * 70)
    print("5. Seeding 7-Day Healthy Baseline & Testing 3 Clinical Anomaly Rules")
    print("=" * 70)
    db = SessionLocal()
    cow = db.query(Cow).filter(Cow.tag_id == "COW_01").first()

    today = date.today()

    # Clear previous test summaries and alerts for clean verification
    db.query(DailyActivitySummary).filter(DailyActivitySummary.cow_id == cow.id).delete()
    db.query(ActivityAlert).filter(ActivityAlert.cow_id == cow.id).delete()
    db.commit()

    # Seed 7 days of normal healthy baseline:
    # Eating ~4.8h, Walking ~0.8h, Lying ~11.5h, Standing ~6.9h
    print("Seeding 7-day healthy history...")
    for day_offset in range(7, 0, -1):
        hist_date = today - timedelta(days=day_offset)
        summary = DailyActivitySummary(
            cow_id=cow.id,
            date=hist_date,
            eating_hours=4.80,
            walking_hours=0.80,
            lying_hours=11.50,
            standing_hours=6.90,
            posture_transitions=12,
            total_minutes_recorded=1440
        )
        db.add(summary)
    db.commit()
    print("[PASS] 7-day historical baseline seeded.")

    # -------------------------------------------------------------
    # Scenario A: Sickness / Anorexia (Feeding Drop by 45%)
    # -------------------------------------------------------------
    print("\n--- Testing Scenario A: Acute Sickness (Feeding Deficit) ---")
    today_summary = DailyActivitySummary(
        cow_id=cow.id,
        date=today,
        eating_hours=2.60,      # Dropped from 4.8h (approx -45.8%)
        walking_hours=0.75,
        lying_hours=12.20,
        standing_hours=8.45,
        posture_transitions=10,
        total_minutes_recorded=1440
    )
    db.add(today_summary)
    db.commit()

    eval_resp = client.post(f"/api/v1/activity/cow/COW_01/evaluate-anomalies?target_date={today.isoformat()}&recompute_summary=false")
    assert eval_resp.status_code == 200
    res = eval_resp.json()
    print(f"Status: {res['status']}")
    print(f"Eating Delta: {res['deviations_pct']['eating_delta_pct']}%")
    print(f"Clinical Notes: {res['clinical_notes']}")
    assert res['status'] == "FLAG_FEEDING_DEFICIT", f"Expected FLAG_FEEDING_DEFICIT, got {res['status']}"
    print("[PASS] Scenario A: Feeding Deficit correctly detected!")

    # -------------------------------------------------------------
    # Scenario B: Estrus / Standing Heat (Walking +150%, Lying -40%)
    # -------------------------------------------------------------
    print("\n--- Testing Scenario B: Estrus / Standing Heat ---")
    today_summary.eating_hours = 4.20
    today_summary.walking_hours = 2.10    # Surge from 0.8h (+162.5%)
    today_summary.lying_hours = 6.80      # Drop from 11.5h (-40.9%)
    today_summary.standing_hours = 10.90
    db.commit()

    eval_resp = client.post(f"/api/v1/activity/cow/COW_01/evaluate-anomalies?target_date={today.isoformat()}&recompute_summary=false")
    assert eval_resp.status_code == 200
    res = eval_resp.json()
    print(f"Status: {res['status']}")
    print(f"Walking Delta: +{res['deviations_pct']['walking_delta_pct']}%")
    print(f"Lying Delta: {res['deviations_pct']['lying_delta_pct']}%")
    print(f"Clinical Notes: {res['clinical_notes']}")
    assert res['status'] == "FLAG_ESTRUS_RESTLESSNESS", f"Expected FLAG_ESTRUS_RESTLESSNESS, got {res['status']}"
    print("[PASS] Scenario B: Estrus Restlessness correctly detected!")

    # -------------------------------------------------------------
    # Scenario C: Lameness (Lying > 14h, Walking Drop -35%)
    # -------------------------------------------------------------
    print("\n--- Testing Scenario C: Lameness / Hoof Injury ---")
    today_summary.eating_hours = 4.00
    today_summary.walking_hours = 0.50    # Dropped from 0.8h (-37.5%)
    today_summary.lying_hours = 15.50     # Exceeds 14.0h threshold
    today_summary.standing_hours = 4.00
    db.commit()

    eval_resp = client.post(f"/api/v1/activity/cow/COW_01/evaluate-anomalies?target_date={today.isoformat()}&recompute_summary=false")
    assert eval_resp.status_code == 200
    res = eval_resp.json()
    print(f"Status: {res['status']}")
    print(f"Lying Hours: {res['current_time_budget']['lying_hours']}h/day")
    print(f"Walking Delta: {res['deviations_pct']['walking_delta_pct']}%")
    print(f"Clinical Notes: {res['clinical_notes']}")
    assert res['status'] == "FLAG_EXCESSIVE_LYING_LAMENESS", f"Expected FLAG_EXCESSIVE_LYING_LAMENESS, got {res['status']}"
    print("[PASS] Scenario C: Lameness correctly detected!")

    # Query all persisted alerts
    alerts_resp = client.get("/api/v1/activity/cow/COW_01/alerts")
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    print(f"\n[PASS] Persisted Health Alerts in Database: {len(alerts)} alerts logged.")

    db.close()
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED SUCCESSFULLY! BACKEND PIPELINE VERIFIED.")
    print("=" * 70)

if __name__ == "__main__":
    test_full_pipeline()
