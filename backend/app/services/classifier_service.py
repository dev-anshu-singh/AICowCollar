import os
import json
import numpy as np
import pandas as pd
import joblib
from typing import Dict, List, Tuple
from ..config import settings

class ClassifierService:
    def __init__(self):
        self.model = None
        self.feature_names = []
        self.target_classes = []
        self.class_to_idx = {}
        self.idx_to_class = {}
        self.load_model()

    def load_model(self):
        if not os.path.exists(settings.MODEL_FILE_PATH):
            raise FileNotFoundError(f"Champion model not found at: {settings.MODEL_FILE_PATH}")
        
        self.model = joblib.load(settings.MODEL_FILE_PATH)
        
        if os.path.exists(settings.METADATA_FILE_PATH):
            with open(settings.METADATA_FILE_PATH, "r") as f:
                metadata = json.load(f)
                self.feature_names = metadata.get("feature_names", [])
                self.target_classes = metadata.get("target_classes", ["lying", "standing", "eating", "walking"])
                self.class_to_idx = metadata.get("class_to_idx", {})
                self.idx_to_class = {int(k): v for k, v in metadata.get("idx_to_class", {}).items()}
        else:
            self.target_classes = ["lying", "standing", "eating", "walking"]
            self.idx_to_class = {0: "lying", 1: "standing", 2: "eating", 3: "walking"}
            self.feature_names = [
                "Mean_accX", "Min_accX", "Mean_accY", "RMS_accY", "Mean_accZ",
                "Mean_SVM_gyro", "Min_SVM_gyro", "Max_SVM_gyro",
                "IQR_gyroY", "IQR_gyroZ", "Mean_SVM_acc", "Sd_SVM_acc"
            ]

    def extract_12_features_from_buffer(self, raw_buffer: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Converts 6 raw 10-second readings (1-minute buffer) into the 12 core physical features.
        Each element in raw_buffer must have keys: accX, accY, accZ, gyroX, gyroY, gyroZ
        """
        df = pd.DataFrame(raw_buffer)
        
        # Calculate Euclidean magnitudes
        svm_gyro = np.sqrt(df['gyroX']**2 + df['gyroY']**2 + df['gyroZ']**2)
        svm_acc = np.sqrt(df['accX']**2 + df['accY']**2 + df['accZ']**2)
        
        def iqr(x):
            q75, q25 = np.percentile(x, [75, 25])
            return float(q75 - q25)
        
        features = {
            "Mean_accX": float(df['accX'].mean()),
            "Min_accX": float(df['accX'].min()),
            "Mean_accY": float(df['accY'].mean()),
            "RMS_accY": float(np.sqrt(np.mean(df['accY']**2))),
            "Mean_accZ": float(df['accZ'].mean()),
            
            "Mean_SVM_gyro": float(svm_gyro.mean()),
            "Min_SVM_gyro": float(svm_gyro.min()),
            "Max_SVM_gyro": float(svm_gyro.max()),
            
            "IQR_gyroY": iqr(df['gyroY']),
            "IQR_gyroZ": iqr(df['gyroZ']),
            
            "Mean_SVM_acc": float(svm_acc.mean()),
            "Sd_SVM_acc": float(svm_acc.std(ddof=1) if len(svm_acc) > 1 else 0.0)
        }
        return features

    def predict_behavior(self, features: Dict[str, float]) -> Tuple[str, float, Dict[str, float]]:
        """
        Takes 12 core physical features and predicts the behavioral class.
        Returns: (predicted_behavior, confidence, probabilities_dict)
        """
        # Ensure correct ordering
        vector = np.array([[features[k] for k in self.feature_names]])
        
        probabilities = self.model.predict_proba(vector)[0]
        pred_idx = int(np.argmax(probabilities))
        confidence = float(probabilities[pred_idx])
        pred_behavior = self.idx_to_class.get(pred_idx, self.target_classes[pred_idx])
        
        probs_dict = {
            self.idx_to_class.get(i, self.target_classes[i]): float(p)
            for i, p in enumerate(probabilities)
        }
        
        return pred_behavior, confidence, probs_dict

# Singleton instance
classifier_service = ClassifierService()
