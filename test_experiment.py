import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier, ExtraTreesClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score, accuracy_score

print("Loading dataset...")
df = pd.read_csv('cow-behavior-classification-acc-gyro-combined/cow_data_processed_updated.csv')
print(f"Loaded shape: {df.shape}")

# Consolidate behaviors exactly as Pongsanun et al. did
behavior_mapping = {
    'lying ruminating': 'lying',
    'lying other': 'lying',
    'standing ruminating': 'standing',
    'standing other': 'standing',
    'walking ruminating': 'walking',
}
df['Classification'] = df['Classification'].replace(behavior_mapping)
df = df[df['Classification'].isin(['lying', 'standing', 'walking', 'eating'])].copy()

behavior_map = {'lying': 0, 'standing': 1, 'eating': 2, 'walking': 3}
y = df['Classification'].map(behavior_map)

# Exclude metadata columns
exclude_cols = ['ID', 'Time', 'Sensor', 'Classification', 'Lying', 'Lying down', 
                'Standing', 'Standing up', 'Walking', 'Feeding', 'Dringking', 'Ruminating', 'Other']
# Also exclude Cumulative columns because they leak row-order time
cumulative_cols = [c for c in df.columns if 'Cumulative' in c]
all_feature_cols = [c for c in df.columns if c not in exclude_cols and c not in cumulative_cols]

print(f"Total non-leaking feature candidates: {len(all_feature_cols)}")

X_all = df[all_feature_cols].fillna(0)
X_train, X_test, y_train, y_test = train_test_split(X_all, y, test_size=0.2, stratify=y, random_state=42)

# Experiment 1: All Available Features (Pongsanun full set)
rf_full = RandomForestClassifier(n_estimators=100, max_depth=12, class_weight='balanced', random_state=42, n_jobs=-1)
rf_full.fit(X_train, y_train)
y_pred_full = rf_full.predict(X_test)
print("\n" + "="*60)
print(f"1. ALL FEATURES ({len(all_feature_cols)} features)")
print(f"Accuracy: {accuracy_score(y_test, y_pred_full):.4f}, Macro-F1: {f1_score(y_test, y_pred_full, average='macro'):.4f}")
print(classification_report(y_test, y_pred_full, target_names=['lying', 'standing', 'eating', 'walking'], digits=4))

# Rank features by importance
importances = pd.Series(rf_full.feature_importances_, index=all_feature_cols).sort_values(ascending=False)
print("\nTop 20 Features by Gini Importance:")
for feat, imp in importances.head(20).items():
    print(f"  {feat:25s}: {imp:.4f}")

# Experiment 2: Pongsanun Top 15 (as used in their code n=15)
top15 = importances.head(15).index.tolist()
rf_15 = RandomForestClassifier(n_estimators=100, max_depth=12, class_weight='balanced', random_state=42, n_jobs=-1)
rf_15.fit(X_train[top15], y_train)
y_pred_15 = rf_15.predict(X_test[top15])
print("\n" + "="*60)
print(f"2. PONGSANUN TOP 15 FEATURES (RFE Top 15)")
print(f"Accuracy: {accuracy_score(y_test, y_pred_15):.4f}, Macro-F1: {f1_score(y_test, y_pred_15, average='macro'):.4f}")
print(classification_report(y_test, y_pred_15, target_names=['lying', 'standing', 'eating', 'walking'], digits=4))

# Experiment 3: Streamlined 10 Core Physical Features
# Physically chosen: 3 gravity tilt (Acc means) + 2 SVM energy (Acc & Gyro) + dynamic spreads
core10 = [
    'Mean_accY',     # Vertical tilt (lying vs standing)
    'Mean_accX',     # Longitudinal pitch (eating vs standing)
    'Mean_accZ',     # Lateral tilt
    'Mean_SVM_gyro', # Overall angular rotation rate
    'Mean_SVM_acc',  # Overall linear acceleration magnitude
    'Sd_SVM_gyro',   # Angular rotation spread/bursts
    'Sd_SVM_acc',    # Linear acceleration spread
    'Sd_accX',       # Stepping/walking forward-backward jerk
    'Sd_gyroY',      # Pitch angular rate variation (chewing oscillation)
    'RMS_accY'       # Vertical kinetic power
]
core10_valid = [c for c in core10 if c in df.columns]
rf_10 = RandomForestClassifier(n_estimators=100, max_depth=12, class_weight='balanced', random_state=42, n_jobs=-1)
rf_10.fit(X_train[core10_valid], y_train)
y_pred_10 = rf_10.predict(X_test[core10_valid])
print("\n" + "="*60)
print(f"3. STREAMLINED 10 CORE FEATURES (Random Forest)")
print(f"Accuracy: {accuracy_score(y_test, y_pred_10):.4f}, Macro-F1: {f1_score(y_test, y_pred_10, average='macro'):.4f}")
print(classification_report(y_test, y_pred_10, target_names=['lying', 'standing', 'eating', 'walking'], digits=4))

# Experiment 4: Streamlined 10 Features with HistGradientBoosting (Boosting Trees)
hgb_10 = HistGradientBoostingClassifier(max_iter=150, max_depth=8, class_weight='balanced', random_state=42)
hgb_10.fit(X_train[core10_valid], y_train)
y_pred_hgb = hgb_10.predict(X_test[core10_valid])
print("\n" + "="*60)
print(f"4. STREAMLINED 10 CORE FEATURES (HistGradientBoosting / LightGBM)")
print(f"Accuracy: {accuracy_score(y_test, y_pred_hgb):.4f}, Macro-F1: {f1_score(y_test, y_pred_hgb, average='macro'):.4f}")
print(classification_report(y_test, y_pred_hgb, target_names=['lying', 'standing', 'eating', 'walking'], digits=4))

# Experiment 5: Ultra-minimal 6 Features
core6 = ['Mean_accY', 'Mean_accX', 'Mean_SVM_gyro', 'Mean_SVM_acc', 'Sd_SVM_gyro', 'Sd_accX']
rf_6 = RandomForestClassifier(n_estimators=100, max_depth=12, class_weight='balanced', random_state=42, n_jobs=-1)
rf_6.fit(X_train[core6], y_train)
y_pred_6 = rf_6.predict(X_test[core6])
print("\n" + "="*60)
print(f"5. ULTRA-MINIMAL 6 FEATURES (Random Forest)")
print(f"Accuracy: {accuracy_score(y_test, y_pred_6):.4f}, Macro-F1: {f1_score(y_test, y_pred_6, average='macro'):.4f}")
print(classification_report(y_test, y_pred_6, target_names=['lying', 'standing', 'eating', 'walking'], digits=4))
