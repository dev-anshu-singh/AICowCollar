import os
import json
import shutil
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sklearn.preprocessing import StandardScaler
from sklearn.mixture import GaussianMixture
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
EVAL_DIR = os.path.join(BASE_DIR, "evaluation_data")
MODEL_DIR = os.path.join(BASE_DIR, "models")
PLOT_DIR = os.path.join(BASE_DIR, "plots")
BACKEND_MODEL_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "backend", "ml_models"))

for d in [DATA_DIR, EVAL_DIR, MODEL_DIR, PLOT_DIR, BACKEND_MODEL_DIR]:
    os.makedirs(d, exist_ok=True)


CSV_URL = "https://raw.githubusercontent.com/Open-Source-Range/OSR_GPS_Collar/refs/heads/master/Data/V1/Example1.GPSLOG.CSV"
COLS = ['id', 'lat', 'lon', 'sats', 'date', 'time', 'ttf_ms', 'm1', 'm2']

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

def is_inside_polygon(lat, lon, polygon):
    inside = False
    n = len(polygon)
    p1_lat, p1_lon = polygon[0]
    for i in range(1, n + 1):
        p2_lat, p2_lon = polygon[i % n]
        if lon > min(p1_lon, p2_lon) and lon <= max(p1_lon, p2_lon) and lat <= max(p1_lat, p2_lat):
            if p1_lon != p2_lon:
                x_inters = (lon - p1_lon) * (p2_lat - p1_lat) / (p2_lon - p1_lon) + p1_lat
            if p1_lat == p2_lat or lat <= x_inters:
                inside = not inside
        p1_lat, p1_lon = p2_lat, p2_lon
    return inside

print("1. Loading and cleaning GPS data...")
df = pd.read_csv(CSV_URL, names=COLS, engine='python').dropna(subset=['lat', 'lon', 'sats', 'date', 'time'])
for c in COLS:
    df[c] = pd.to_numeric(df[c], errors='coerce')
df = df[(df['sats'] >= 3) & (df['lat'].between(-90, 90)) & (df['lon'].between(-180, 180))].copy()

date_str = df['date'].astype(int).astype(str).str.zfill(6)
time_str = df['time'].astype(int).astype(str).str.zfill(8).str[:6]
df['timestamp'] = pd.to_datetime(date_str + time_str, format='%d%m%y%H%M%S', errors='coerce')
df = df.dropna(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)

for _ in range(3):
    dt = df['timestamp'].diff().dt.total_seconds()
    spd = haversine_m(df['lat'].shift(1), df['lon'].shift(1), df['lat'], df['lon']) / dt
    df = df[(spd.isna()) | (spd <= 2.5)].reset_index(drop=True)

df['dt_sec'] = df['timestamp'].diff().dt.total_seconds()
df['step_m'] = haversine_m(df['lat'].shift(1), df['lon'].shift(1), df['lat'], df['lon'])
df['speed_mps'] = df['step_m'] / df['dt_sec']
df = df[(df['dt_sec'] > 0) & (df['dt_sec'] <= 1800)].copy()

df['bearing'] = bearing_deg(df['lat'].shift(1), df['lon'].shift(1), df['lat'], df['lon'])
raw_turn = np.abs(df['bearing'].diff())
df['turn_angle'] = np.where(raw_turn > 180, 360 - raw_turn, raw_turn)

W = 6
df['speed_mean'] = df['speed_mps'].rolling(W).mean()
df['speed_std'] = df['speed_mps'].rolling(W).std()
df['turn_std'] = df['turn_angle'].rolling(W).std()
net_m = haversine_m(df['lat'].shift(W), df['lon'].shift(W), df['lat'], df['lon'])
df['straightness'] = (net_m / (df['step_m'].rolling(W).sum() + 1e-5)).clip(0, 1)
df['ttf_sec'] = df['ttf_ms'] / 1000.0
df = df.dropna().reset_index(drop=True)

print("2. Training GMM Behavior Classifier...")
features = ['speed_mean', 'speed_std', 'turn_std', 'straightness', 'ttf_sec']
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[features])

gmm = GaussianMixture(n_components=3, covariance_type='full', random_state=42)
df['cluster'] = gmm.fit_predict(X_scaled)
order = df.groupby('cluster')['speed_mean'].mean().sort_values().index
label_map = {int(order[0]): 'Resting', int(order[1]): 'Grazing', int(order[2]): 'Walking'}
df['behavior'] = df['cluster'].map(label_map)

df.to_csv(os.path.join(DATA_DIR, "cow_gps_processed.csv"), index=False)

model_path = os.path.join(MODEL_DIR, "cow_collar_gps_model.joblib")
joblib.dump({'scaler': scaler, 'gmm': gmm, 'label_map': label_map, 'features': features}, model_path)
shutil.copy(model_path, os.path.join(BACKEND_MODEL_DIR, "cow_collar_gps_model.joblib"))

metadata = {
    "model_name": "GMM_GPS_Behavior_And_Geofence",
    "window_fixes": W,
    "features": features,
    "classes": ["Resting", "Grazing", "Walking"],
    "geofence_debounce_strikes": 2,
    "max_speed_filter_mps": 2.5
}
for target_dir in [MODEL_DIR, BACKEND_MODEL_DIR]:
    with open(os.path.join(target_dir, "gps_feature_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

print("3. Evaluating Metrics...")
conds = [
    (df['speed_mean'] < 0.05),
    (df['speed_mean'] >= 0.05) & (df['speed_mean'] <= 0.35) & (df['straightness'] < 0.70)
]
y_true_beh = np.select(conds, ['Resting', 'Grazing'], default='Walking')
with open(os.path.join(EVAL_DIR, "gps_behavior_metrics.json"), "w") as f:
    json.dump(classification_report(y_true_beh, df['behavior'], output_dict=True), f, indent=2)

c_lat, c_lon = float(df['lat'].median()), float(df['lon'].median())
FARM_POLYGON = [
    (c_lat + 0.003, c_lon - 0.004),
    (c_lat + 0.003, c_lon + 0.004),
    (c_lat - 0.003, c_lon + 0.004),
    (c_lat - 0.003, c_lon - 0.004),
]
np.random.seed(42)
y_true_breach = np.array([not is_inside_polygon(lat, lon, FARM_POLYGON) for lat, lon in zip(df['lat'], df['lon'])])
noisy_lat = df['lat'].copy() + np.random.normal(0, 0.00007, len(df))
noisy_lon = df['lon'].copy() + np.random.normal(0, 0.00007, len(df))
spike_