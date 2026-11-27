import os
import joblib
import numpy as np
import pandas as pd

MODEL_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "ml_models", "cow_collar_gps_model.joblib")
)
_bundle = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None

DEFAULT_FARM_POLYGON = [
    (42.567500, -113.796000),
    (42.567500, -113.786000),
    (42.561000, -113.786000),
    (42.561000, -113.796000),
]

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = np.radians(lat2 - lat1), np.radians(lon2 - lon1)
    a = np.sin(dp / 2)**2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2)**2
    return 2 * R * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

def bearing_deg(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dl = np.radians(lon2 - lon1)
    y = np.sin(dl) * np.cos(p2)
    x = np.cos(p1) * np.sin(p2) - np.sin(p1) * np.cos(p2) * np.cos(dl)
    return np.degrees(np.arctan2(y, x))

def is_inside_polygon(lat: float, lon: float, polygon: list) -> bool:
    """Ray-Casting Point-in-Polygon boundary check."""
    inside = False
    n = len(polygon)
    p1_lat, p1_lon = polygon[0]
    for i in range(1, n + 1):
        p2_lat, p2_lon = polygon[i % n]
        if lon > min(p1_lon, p2_lon):
            if lon <= max(p1_lon, p2_lon):
                if lat <= max(p1_lat, p2_lat):
                    if p1_lon != p2_lon:
                        x_inters = (lon - p1_lon) * (p2_lat - p1_lat) / (p2_lon - p1_lon) + p1_lat
                    if p1_lat == p2_lat or lat <= x_inters:
                        inside = not inside
        p1_lat, p1_lon = p2_lat, p2_lon
    return inside

def evaluate_gps_window(recent_fixes: list, polygon: list = DEFAULT_FARM_POLYGON) -> dict:
    """Evaluates 7 consecutive GPS fixes for 2-strike polygon geofence breach & GMM behavior."""
    df = pd.DataFrame(recent_fixes)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)

    outside_flags = [not is_inside_polygon(row.lat, row.lon, polygon) for row in df.itertuples()]
    confirmed_breach = bool(len(outside_flags) >= 2 and outside_flags[-1] and outside_flags[-2])

    dt = df['timestamp'].diff().dt.total_seconds()
    step_m = haversine_m(df['lat'].shift(1), df['lon'].shift(1), df['lat'], df['lon'])
    speed_mps = step_m / dt

    bearing = bearing_deg(df['lat'].shift(1), df['lon'].shift(1), df['lat'], df['lon'])
    raw_turn = np.abs(bearing.diff())
    turn_angle = np.where(raw_turn > 180, 360 - raw_turn, raw_turn)

    W = 6
    net_m = haversine_m(df['lat'].iloc[-W-1], df['lon'].iloc[-W-1], df['lat'].iloc[-1], df['lon'].iloc[-1])
    path_m = step_m.iloc[-W:].sum()

    behavior = "Unknown"
    if _bundle is not None:
        X_live = pd.DataFrame([{
            'speed_mean': float(speed_mps.iloc[-W:].mean()),
            'speed_std': float(speed_mps.iloc[-W:].std()),
            'turn_std': float(pd.Series(turn_angle).iloc[-W:].std()),
            'straightness': float(np.clip(net_m / (path_m + 1e-5), 0, 1)),
            'ttf_sec': float(df['ttf_ms'].iloc[-1]) / 1000.0
        }])
        cluster = _bundle['gmm'].predict(_bundle['scaler'].transform(X_live))[0]
        behavior = str(_bundle['label_map'][cluster])

    return {
        "timestamp": str(df['timestamp'].iloc[-1]),
        "lat": float(df['lat'].iloc[-1]),
        "lon": float(df['lon'].iloc[-1]),
        "gps_behavior": behavior,
        "is_outside_now": bool(outside_flags[-1]),
        "geofence_alert": confirmed_breach,
        "alert_message": "ALERT: Cow crossed farm boundary!" if confirmed_breach else "OK: Inside farm boundary"
    }