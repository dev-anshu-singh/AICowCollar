import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import classification_report, f1_score, accuracy_score

df = pd.read_csv('cow-behavior-classification-acc-gyro-combined/cow_data_processed_updated.csv')

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

# Exclude metadata and non-causal columns
exclude_cols = ['ID', 'Time', 'Sensor', 'Classification', 'Lying', 'Lying down', 'Standing', 'Standing up', 'Walking', 'Feeding', 'Dringking', 'Ruminating', 'Other']
cumulative_cols = [c for c in df.columns if 'Cumulative' in c]
all_feature_cols = [c for c in df.columns if c not in exclude_cols and c not in cumulative_cols]

print(f'Total valid feature candidates: {len(all_feature_cols)}')

# Train test split
X_all = df[all_feature_cols].fillna(0)
X_train, X_test, y_train, y_test = train_test_split(X_all, y, test_size=0.2, stratify=y, random_state=42)

# 1. Full Features Random Forest
rf_full = RandomForestClassifier(n_estimators=100, max_depth=12, class_weight='balanced', random_state=42, n_jobs=-1)
rf_full.fit(X_train, y_train)
y_pred_full = rf_full.predict(X_test)
acc_full = accuracy_score(y_test, y_pred_full)
f1_macro_full = f1_score(y_test, y_pred_full, average='macro')
f1_weighted_full = f1_score(y_test, y_pred_full, average='weighted')

print('\n=== 1. FULL FEATURES (124 features) ===')
print(f'Accuracy: {acc_full:.4f}, F1-Macro: {f1_macro_full:.4f}, F1-Weighted: {f1_weighted_full:.4f}')
print(classification_report(y_test, y_pred_full, target_names=['lying', 'standing', 'eating', 'walking'], digits=4))

# Get top features
importances = pd.Series(rf_full.feature_importances_, index=all_feature_cols).sort_values(ascending=False)
print('\nTop 20 Features by Gini Importance:')
for feat, imp in importances.head(20).items():
    print(f'  {feat:25s}: {imp:.4f}')

# 2. Pongsanun Top 15 Features
top15 = importances.head(15).index.tolist()
rf_15 = RandomForestClassifier(n_estimators=100, max_depth=12, class_weight='balanced', random_state=42, n_jobs=-1)
rf_15.fit(X_train[top15], y_train)
y_pred_15 = rf_15.predict(X_test[top15])
print('\n=== 2. TOP 15 FEATURES (as in Pongsanun RFE) ===')
print(f'Accuracy: {accuracy_score(y_test, y_pred_15):.4f}, F1-Macro: {f1_score(y_test, y_pred_15, average="macro"):.4f}')
print(classification_report(y_test, y_pred_15, target_names=['lying', 'standing', 'eating', 'walking'], digits=4))

# 3. Lean Handcrafted / Intuitive Set (10 Core Features)
core10 = [
    'Mean_accY',     # Gravitational vertical inclination (standing vs lying)
    'Mean_accX',     # Longitudinal tilt (eating head-down vs standing)
    'Mean_accZ',     # Lateral neck tilt
    'Mean_SVM_gyro', # Overall angular velocity (static posture vs dynamic activity)
    'Mean_SVM_acc',  # Overall linear acceleration magnitude
    'Sd_SVM_gyro',   # Rotational variability
    'Sd_SVM_acc',    # Linear acceleration variability / movement burst
    'Sd_accX',       # Forward-backward jerk (stepping/walking)
    'Sd_gyroY',      # Pitch angular rate variation (chewing/grazing oscillation)
    'RMS_accY'       # Vertical kinetic energy
]

core10_valid = [c for c in core10 if c in df.columns]
print(f'\nCore 10 features available: {len(core10_valid)}/{len(core10)}')

rf_core10 = RandomForestClassifier(n_estimators=100, max_depth=12, class_weight='balanced', random_state=42, n_jobs=-1)
rf_core10.fit(X_train[core10_valid], y_train)
y_pred_core10 = rf_core10.predict(X_test[core10_valid])
print('\n=== 3. STREAMLINED 10 CORE FEATURES (Random Forest) ===')
print(f'Accuracy: {accuracy_score(y_test, y_pred_core10):.4f}, F1-Macro: {f1_score(y_test, y_pred_core10, average="macro"):.4f}')
print(classification_report(y_test, y_pred_core10, target_names=['lying', 'standing', 'eating', 'walking'], digits=4))

# 4. Streamlined 10 Core Features with Gradient Boosting (HistGradientBoosting)
hgb_core10 = HistGradientBoostingClassifier(max_iter=150, max_depth=8, class_weight='balanced', random_state=42)
hgb_core10.fit(X_train[core10_valid], y_train)
y_pred_hgb = hgb_core10.predict(X_test[core10_valid])
print('\n=== 4. STREAMLINED 10 CORE FEATURES (HistGradientBoosting) ===')
print(f'Accuracy: {accuracy_score(y_test, y_pred_hgb):.4f}, F1-Macro: {f1_score(y_test, y_pred_hgb, average="macro"):.4f}')
print(classification_report(y_test, y_pred_hgb, target_names=['lying', 'standing', 'eating', 'walking'], digits=4))

# 5. Ultra-minimal 6 Features (Only Acc + Gyro Means and SVMs)
core6 = ['Mean_accY', 'Mean_accX', 'Mean_SVM_gyro', 'Mean_SVM_acc', 'Sd_SVM_gyro', 'Sd_accX']
rf_core6 = RandomForestClassifier(n_estimators=100, max_depth=12, class_weight='balanced', random_state=42, n_jobs=-1)
rf_core6.fit(X_train[core6], y_train)
y_pred_core6 = rf_core6.predict(X_test[core6])
print('\n=== 5. ULTRA-MINIMAL 6 FEATURES (Random Forest) ===')
print(f'Accuracy: {accuracy_score(y_test, y_pred_core6):.4f}, F1-Macro: {f1_score(y_test, y_pred_core6, average="macro"):.4f}')
print(classification_report(y_test, y_pred_core6, target_names=['lying', 'standing', 'eating', 'walking'], digits=4))

# 6. Engineered Non-Redundant 12 Features
best12 = [
    'Mean_accX', 'Min_accX',
    'Mean_accY', 'RMS_accY',
    'Mean_accZ',
    'Mean_SVM_gyro', 'Min_SVM_gyro', 'Max_SVM_gyro',
    'IQR_gyroY', 'IQR_gyroZ',
    'Mean_SVM_acc', 'Sd_SVM_acc'
]
rf_12 = RandomForestClassifier(n_estimators=120, max_depth=12, class_weight='balanced', random_state=42, n_jobs=-1)
rf_12.fit(X_train[best12], y_train)
y_pred_12 = rf_12.predict(X_test[best12])
print('\n=== 6. ENGINEERED NON-REDUNDANT 12 FEATURES (Random Forest) ===')
print(f'Accuracy: {accuracy_score(y_test, y_pred_12):.4f}, F1-Macro: {f1_score(y_test, y_pred_12, average="macro"):.4f}')
print(classification_report(y_test, y_pred_12, target_names=['lying', 'standing', 'eating', 'walking'], digits=4))

et_12 = ExtraTreesClassifier(n_estimators=120, max_depth=14, class_weight='balanced', random_state=42, n_jobs=-1)
et_12.fit(X_train[best12], y_train)
y_pred_et12 = et_12.predict(X_test[best12])
print('\n=== 7. ENGINEERED NON-REDUNDANT 12 FEATURES (Extra Trees) ===')
print(f'Accuracy: {accuracy_score(y_test, y_pred_et12):.4f}, F1-Macro: {f1_score(y_test, y_pred_et12, average="macro"):.4f}')
print(classification_report(y_test, y_pred_et12, target_names=['lying', 'standing', 'eating', 'walking'], digits=4))

