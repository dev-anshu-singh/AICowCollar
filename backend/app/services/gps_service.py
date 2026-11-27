import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional, List
from sqlalchemy.orm import Session

from ..models.cow import Cow
from ..models.gps import GPSRecord, GPSAlert

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

def is_inside_polygon(lat: float, lon: float, polygon: list = DEFAULT_FARM_POLYGON) -> bool:
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
    """Evaluates consecutive GPS fixes for 2-strike polygon geofence breach & GMM behavior."""
    df = pd.DataFrame(recent_fixes)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.sort_values('timestamp').reset_index(drop=True)

    outside_flags = [not is_inside_polygon(row.lat, row.lon, polygon) for row in df.itertuples()]
    confirmed_breach = bool(len(outside_flags) >= 2 and outside_flags[-1] and outside_flags[-2])

    dt = df['timestamp'].diff().dt.total_seconds().replace(0, 1.0)
    step_m = haversine_m(df['lat'].shift(1), df['lon'].shift(1), df['lat'], df['lon']).fillna(0.0)
    speed_mps = (step_m / dt).fillna(0.0)

    bearing = bearing_deg(df['lat'].shift(1), df['lon'].shift(1), df['lat'], df['lon']).fillna(0.0)
    raw_turn = np.abs(bearing.diff()).fillna(0.0)
    turn_angle = np.where(raw_turn > 180, 360 - raw_turn, raw_turn)

    W = min(6, len(df) - 1)
    net_m = haversine_m(df['lat'].iloc[-W-1], df['lon'].iloc[-W-1], df['lat'].iloc[-1], df['lon'].iloc[-1])
    path_m = step_m.iloc[-W:].sum()

    behavior = "Unknown"
    if _bundle is not None and W >= 2:
        try:
            X_live = pd.DataFrame([{
                'speed_mean': float(speed_mps.iloc[-W:].mean()),
                'speed_std': float(speed_mps.iloc[-W:].std() if len(speed_mps.iloc[-W:]) > 1 else 0.0),
                'turn_std': float(pd.Series(turn_angle).iloc[-W:].std() if len(turn_angle) > 1 else 0.0),
                'straightness': float(np.clip(net_m / (path_m + 1e-5), 0, 1)),
                'ttf_sec': float(df['ttf_ms'].iloc[-1]) / 1000.0 if 'ttf_ms' in df.columns else 1.0
            }])
            X_live = X_live.fillna(0.0)
            cluster = _bundle['gmm'].predict(_bundle['scaler'].transform(X_live))[0]
            behavior = str(_bundle['label_map'][cluster])
        except Exception:
            behavior = "Unknown"

    latest_speed = float(speed_mps.iloc[-1]) if len(speed_mps) > 0 else 0.0
    latest_ttf = float(df['ttf_ms'].iloc[-1]) if 'ttf_ms' in df.columns else 1000.0

    return {
        "timestamp": df['timestamp'].iloc[-1],
        "lat": float(df['lat'].iloc[-1]),
        "lon": float(df['lon'].iloc[-1]),
        "ttf_ms": latest_ttf,
        "speed_mps": round(latest_speed, 2),
        "gps_behavior": behavior,
        "is_outside_now": bool(outside_flags[-1]),
        "geofence_alert": confirmed_breach,
        "alert_message": "ALERT: Cow crossed farm boundary!" if confirmed_breach else "OK: Inside farm boundary"
    }


class GPSService:
    """
    Service integrating GPS telemetry ingestion, Ray-Casting Polygon Geofencing,
    2-strike breach debounce, and GMM grazing behavior classification into the database.
    """

    @classmethod
    def get_farm_polygon(cls) -> List[Tuple[float, float]]:
        return DEFAULT_FARM_POLYGON

    @classmethod
    def process_telemetry(
        cls,
        cow: Cow,
        fixes: Optional[List[dict]] = None,
        single_fix: Optional[dict] = None,
        polygon: list = DEFAULT_FARM_POLYGON,
        db: Session = None
    ) -> Tuple[GPSRecord, Optional[GPSAlert]]:
        """
        Processes incoming GPS fix/window:
        - If window of fixes is supplied, evaluates directly.
        - If single fix is supplied, fetches previous 6 fixes from DB to construct window.
        - Persists record and deduplicates geofence alerts.
        """
        raw_fixes = []

        if fixes and len(fixes) > 0:
            for f in fixes:
                ts = f.get('timestamp') or datetime.now(timezone.utc)
                raw_fixes.append({
                    'lat': f['lat'],
                    'lon': f['lon'],
                    'timestamp': ts,
                    'ttf_ms': f.get('ttf_ms', 1000.0)
                })
        elif single_fix:
            cur_ts = single_fix.get('timestamp') or datetime.now(timezone.utc)
            cur_fix_dict = {
                'lat': single_fix['lat'],
                'lon': single_fix['lon'],
                'timestamp': cur_ts,
                'ttf_ms': single_fix.get('ttf_ms', 1000.0)
            }
            # Query up to 6 historical fixes for this cow from DB to assemble sliding window
            recent = db.query(GPSRecord).filter(
                GPSRecord.cow_id == cow.id
            ).order_by(GPSRecord.timestamp.desc()).limit(6).all()

            history = [
                {'lat': r.lat, 'lon': r.lon, 'timestamp': r.timestamp, 'ttf_ms': r.ttf_ms or 1000.0}
                for r in reversed(recent)
            ]
            raw_fixes = history + [cur_fix_dict]

        if not raw_fixes:
            raise ValueError("No GPS fixes provided in telemetry payload.")

        # If we have 2 or more fixes, evaluate full trajectory window
        if len(raw_fixes) >= 2:
            eval_res = evaluate_gps_window(raw_fixes, polygon)
            ts_val = eval_res['timestamp']
            if isinstance(ts_val, str):
                ts_naive = pd.to_datetime(ts_val).to_pydatetime().replace(tzinfo=None)
            elif hasattr(ts_val, 'to_pydatetime'):
                ts_naive = ts_val.to_pydatetime().replace(tzinfo=None)
            elif isinstance(ts_val, datetime):
                ts_naive = ts_val.replace(tzinfo=None)
            else:
                ts_naive = datetime.now(timezone.utc).replace(tzinfo=None)

            lat = eval_res['lat']
            lon = eval_res['lon']
            speed = eval_res['speed_mps']
            behavior = eval_res['gps_behavior']
            is_outside = eval_res['is_outside_now']
            breach = eval_res['geofence_alert']
            msg = eval_res['alert_message']
            ttf = eval_res['ttf_ms']
        else:
            # Single isolated fix without prior history
            f = raw_fixes[0]
            lat = f['lat']
            lon = f['lon']
            ttf = f.get('ttf_ms', 1000.0)
            ts = f['timestamp']
            ts_naive = ts.replace(tzinfo=None) if hasattr(ts, 'tzinfo') and ts.tzinfo is not None else ts
            is_outside = not is_inside_polygon(lat, lon, polygon)
            breach = False
            speed = 0.0
            behavior = "Unknown"
            msg = "OK: Inside farm boundary" if not is_outside else "Strike 1: First fix outside boundary (awaiting confirmation)"

        # Save GPSRecord
        record = GPSRecord(
            cow_id=cow.id,
            timestamp=ts_naive,
            lat=round(lat, 6),
            lon=round(lon, 6),
            ttf_ms=ttf,
            speed_mps=speed,
            gps_behavior=behavior,
            is_outside=is_outside,
            geofence_breach=breach,
            alert_message=msg
        )
        db.add(record)
        db.flush()

        alert = None
        # Handle Geofence Breach Alert (2-strike debounced)
        if breach:
            # Deduplicate alert within 2 hours
            recent_alert = db.query(GPSAlert).filter(
                GPSAlert.cow_id == cow.id,
                GPSAlert.alert_type == "GEOFENCE_BREACH",
                GPSAlert.timestamp >= ts_naive - timedelta(hours=2)
            ).first()

            if not recent_alert:
                alert = GPSAlert(
                    cow_id=cow.id,
                    timestamp=ts_naive,
                    alert_type="GEOFENCE_BREACH",
                    severity="CRITICAL",
                    lat=round(lat, 6),
                    lon=round(lon, 6),
                    message=msg,
                    acknowledged=False
                )
                db.add(alert)
                db.flush()

        db.commit()
        db.refresh(record)
        if alert:
            db.refresh(alert)

        return record, alert

gps_service = GPSService()
