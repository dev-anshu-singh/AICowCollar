import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Cow, GPSRecord, GPSAlert
from app.services.gps_service import DEFAULT_FARM_POLYGON, evaluate_gps_window

client = TestClient(app)

def run_gps_tests():
    print("=" * 70)
    print("STARTING GPS & GEOFENCING INTEGRATION TEST SUITE")
    print("=" * 70)

    # 1. Root & Health Check
    print("\n--- 1. Testing System Health & GPS Endpoints ---")
    resp = client.get("/")
    assert resp.status_code == 200
    endpoints = resp.json()["endpoints"]
    assert "gps_telemetry" in endpoints
    assert "gps_records" in endpoints
    assert "gps_alerts" in endpoints
    assert "gps_farm_polygon" in endpoints
    print("[PASS] GPS endpoints successfully mounted in FastAPI application.")

    # 2. Farm Polygon retrieval
    print("\n--- 2. Testing Farm Boundary Polygon Endpoint ---")
    poly_resp = client.get("/api/v1/gps/farm-polygon")
    assert poly_resp.status_code == 200
    poly_data = poly_resp.json()
    assert poly_data["total_vertices"] == 4
    print(f"[PASS] Farm polygon retrieved: {poly_data['total_vertices']} vertices.")

    # 3. Clean and Register Test Cow
    tag_id = "COW_GPS_01"
    db = SessionLocal()
    cow = db.query(Cow).filter(Cow.tag_id == tag_id).first()
    if cow:
        db.query(GPSRecord).filter(GPSRecord.cow_id == cow.id).delete()
        db.query(GPSAlert).filter(GPSAlert.cow_id == cow.id).delete()
        db.commit()
    db.close()

    client.post("/api/v1/cows/", json={"tag_id": tag_id, "name": "Bessie - GPS Test", "breed": "Holstein"})

    # 4. Ingest Window of Fixes inside Polygon (Normal Grazing / Walking)
    print("\n--- 3. Testing Normal Fixes Inside Pasture (No Breach) ---")
    inside_fixes = [
        {"lat": 42.5650, "lon": -113.7900, "timestamp": "2026-11-27T10:00:00Z", "ttf_ms": 1200},
        {"lat": 42.5655, "lon": -113.7895, "timestamp": "2026-11-27T10:05:00Z", "ttf_ms": 1100},
        {"lat": 42.5662, "lon": -113.7890, "timestamp": "2026-11-27T10:10:00Z", "ttf_ms": 1050},
        {"lat": 42.5670, "lon": -113.7885, "timestamp": "2026-11-27T10:15:00Z", "ttf_ms": 1150},
        {"lat": 42.5674, "lon": -113.7880, "timestamp": "2026-11-27T10:20:00Z", "ttf_ms": 1000},
    ]

    res = client.post("/api/v1/gps/telemetry", json={
        "tag_id": tag_id,
        "fixes": inside_fixes
    })
    assert res.status_code == 201
    rec_data = res.json()
    print(f"  Lat: {rec_data['lat']} | Lon: {rec_data['lon']} | Outside: {rec_data['is_outside']} | Breach: {rec_data['geofence_breach']} | Behavior: {rec_data['gps_behavior']}")
    assert rec_data["is_outside"] is False
    assert rec_data["geofence_breach"] is False
    print("[PASS] Normal pasture telemetry ingested without breach.")

    # 5. Testing 2-Strike Debounce Geofence Breach
    print("\n--- 4. Testing 2-Strike Debounce Geofence Alert Logic ---")
    
    # Strike 1: 1st point outside polygon (lat 42.5680 > 42.567500)
    print("Simulating Strike 1 (First outlier outside boundary)...")
    res_s1 = client.post("/api/v1/gps/telemetry", json={
        "tag_id": tag_id,
        "single_fix": {
            "lat": 42.5680,
            "lon": -113.7875,
            "timestamp": "2026-11-27T10:25:00Z",
            "ttf_ms": 950
        }
    })
    assert res_s1.status_code == 201
    s1_data = res_s1.json()
    print(f"  Strike 1 Result -> is_outside: {s1_data['is_outside']} | geofence_breach: {s1_data['geofence_breach']}")
    assert s1_data["is_outside"] is True
    assert s1_data["geofence_breach"] is False, "Strike 1 alone should NOT trigger confirmed breach!"
    print("[PASS] Strike 1 successfully debounced (No false alarm fired).")

    # Strike 2: 2nd consecutive point outside polygon -> CONFIRMED BREACH ALERT
    print("Simulating Strike 2 (Second consecutive outlier outside boundary)...")
    res_s2 = client.post("/api/v1/gps/telemetry", json={
        "tag_id": tag_id,
        "single_fix": {
            "lat": 42.5688,
            "lon": -113.7870,
            "timestamp": "2026-11-27T10:30:00Z",
            "ttf_ms": 980
        }
    })
    assert res_s2.status_code == 201
    s2_data = res_s2.json()
    print(f"  Strike 2 Result -> is_outside: {s2_data['is_outside']} | geofence_breach: {s2_data['geofence_breach']} | Alert: {s2_data['alert_message']}")
    assert s2_data["is_outside"] is True
    assert s2_data["geofence_breach"] is True, "Strike 2 MUST trigger confirmed breach alert!"
    print("[PASS] Strike 2 correctly confirmed geofence breach alert!")

    # 6. Verify Persisted Alert in Database
    print("\n--- 5. Verifying Persisted Geofence Alert in DB ---")
    alerts_resp = client.get(f"/api/v1/gps/cow/{tag_id}/alerts")
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    assert len(alerts) >= 1
    breach_alert = alerts[0]
    assert breach_alert["alert_type"] == "GEOFENCE_BREACH"
    assert breach_alert["severity"] == "CRITICAL"
    print(f"[PASS] Persisted Alert: {breach_alert['alert_type']} ({breach_alert['severity']}) - {breach_alert['message']}")

    # 7. Query Location Trail Records
    print("\n--- 6. Querying Cow Location History / Breadcrumb Trail ---")
    records_resp = client.get(f"/api/v1/gps/cow/{tag_id}/records")
    assert records_resp.status_code == 200
    history = records_resp.json()
    assert len(history) >= 3
    print(f"[PASS] Retrieved {len(history)} GPS tracking fixes for cow {tag_id}.")

    # 8. Alert Acknowledgment
    print("\n--- 7. Testing Alert Acknowledgment ---")
    ack_res = client.post(f"/api/v1/gps/alerts/{breach_alert['id']}/acknowledge")
    assert ack_res.status_code == 200
    assert ack_res.json()["acknowledged"] is True
    print(f"[PASS] Alert ID {breach_alert['id']} successfully acknowledged.")

    print("\n" + "=" * 70)
    print("ALL GPS & GEOFENCING TESTS PASSED SUCCESSFULLY! ZERO ERRORS.")
    print("=" * 70)

if __name__ == "__main__":
    run_gps_tests()
