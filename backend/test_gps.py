from app.services.gps_service import evaluate_gps_window, DEFAULT_FARM_POLYGON

sample_fixes = [
    {"lat": 42.5650, "lon": -113.7900, "timestamp": "2026-11-27 10:00:00", "ttf_ms": 1200},
    {"lat": 42.5655, "lon": -113.7895, "timestamp": "2026-11-27 10:05:00", "ttf_ms": 1100},
    {"lat": 42.5662, "lon": -113.7890, "timestamp": "2026-11-27 10:10:00", "ttf_ms": 1050},
    {"lat": 42.5670, "lon": -113.7885, "timestamp": "2026-11-27 10:15:00", "ttf_ms": 1150},
    {"lat": 42.5674, "lon": -113.7880, "timestamp": "2026-11-27 10:20:00", "ttf_ms": 1000},
    {"lat": 42.5680, "lon": -113.7875, "timestamp": "2026-11-27 10:25:00", "ttf_ms": 950},   # Strike 1 outside
    {"lat": 42.5688, "lon": -113.7870, "timestamp": "2026-11-27 10:30:00", "ttf_ms": 980},   # Strike 2 outside -> ALERT
]

result = evaluate_gps_window(sample_fixes, DEFAULT_FARM_POLYGON)
print("GPS Geofence & Behavior Test Output:")
print(result)
assert result["geofence_alert"] is True, "Expected geofence breach alert!"
print("PASSED: 2-Strike Polygon Geofence Alert verified.")