#!/usr/bin/env python3
"""Inference wrapper for yield prediction hybrid model."""

import numpy as np
import joblib
import torch
import xgboost as xgb
from pathlib import Path

MODEL_DIR = Path(__file__).parent

FEATURE_NAMES = [
    "soil_ph", "organic_carbon_pct", "available_nitrogen_kg_ha",
    "available_phosphorus_kg_ha", "available_potassium_kg_ha", "soil_moisture_pct",
    "cumulative_rainfall_mm", "mean_temperature_c", "growing_degree_days",
    "relative_humidity_pct", "solar_radiation_mj_m2", "irrigation_area_fraction",
    "fertilizer_rate_kg_ha", "crop_type_encoded", "sowing_week", "harvest_week",
    "previous_season_yield_t_ha", "yield_3yr_moving_avg_t_ha",
]


class YieldPredictor:
    """Production inference for XGBoost-LSTM hybrid yield prediction."""

    def __init__(self, model_dir=None, device=None):
        if model_dir is None:
            model_dir = MODEL_DIR
        self.model_dir = Path(model_dir)
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self._load_models()

    def _load_models(self):
        self.scaler = joblib.load(self.model_dir / "scaler.pkl")

        self.xgb_model = xgb.XGBRegressor()
        self.xgb_model.load_model(str(self.model_dir / "xgboost_model.json"))

        lstm_path = self.model_dir / "lstm_model.pt"
        if lstm_path.exists():
            from train_hybrid import LSTMYieldPredictor
            ckpt = torch.load(lstm_path, map_location=self.device, weights_only=False)
            self.lstm_model = LSTMYieldPredictor(
                ckpt["input_size"], ckpt["hidden_size"], ckpt["num_layers"])
            self.lstm_model.load_state_dict(ckpt["model_state_dict"])
            self.lstm_model.to(self.device).eval()
            self.has_lstm = True
        else:
            self.has_lstm = False

    def predict(self, features_dict):
        """Predict yield from feature dictionary.

        Args:
            features_dict: dict with keys matching FEATURE_NAMES
        Returns:
            dict with prediction, confidence interval, feature importances
        """
        feature_values = np.array([[features_dict.get(f, 0.0) for f in FEATURE_NAMES]],
                                   dtype=np.float32)
        X_scaled = self.scaler.transform(feature_values)

        xgb_pred = float(self.xgb_model.predict(X_scaled)[0])

        if self.has_lstm:
            leaf_idx = self.xgb_model.apply(X_scaled).astype(np.float32)
            seq = np.tile(leaf_idx, (5, 1))[np.newaxis, :, :]
            seq_tensor = torch.FloatTensor(seq).to(self.device)
            with torch.no_grad():
                lstm_pred = float(self.lstm_model(seq_tensor).cpu().numpy()[0])
            final_pred = lstm_pred
        else:
            final_pred = xgb_pred

        std_estimate = abs(final_pred) * 0.08
        ci_lower = max(0, final_pred - 1.96 * std_estimate)
        ci_upper = final_pred + 1.96 * std_estimate

        importances = dict(zip(FEATURE_NAMES, self.xgb_model.feature_importances_))
        sorted_imp = sorted(importances.items(), key=lambda x: x[1], reverse=True)

        return {
            "predicted_yield_t_ha": round(final_pred, 2),
            "confidence_interval": {"lower": round(ci_lower, 2), "upper": round(ci_upper, 2)},
            "xgb_prediction": round(xgb_pred, 2),
            "feature_importances": sorted_imp[:10],
        }

    def predict_batch(self, features_list):
        """Predict for multiple samples."""
        return [self.predict(f) for f in features_list]
