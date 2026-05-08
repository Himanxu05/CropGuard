"""Yield prediction API routes."""

import os
import sys
from flask import Blueprint, request, jsonify, g, current_app
from app import db
from app.models.yield_record import YieldPrediction
from app.middleware.rbac import require_auth, require_permission
from app.middleware.audit import log_audit

yield_bp = Blueprint("yield", __name__)

_predictor = None


def get_predictor():
    global _predictor
    if _predictor is None:
        model_dir = current_app.config.get("YIELD_MODEL_DIR")
        sys.path.insert(0, model_dir)
        try:
            from inference import YieldPredictor
            _predictor = YieldPredictor(model_dir=model_dir)
        except Exception as e:
            current_app.logger.error(f"Failed to load yield model: {e}")
            return None
    return _predictor


REQUIRED_FEATURES = [
    "soil_ph", "organic_carbon_pct", "available_nitrogen_kg_ha",
    "available_phosphorus_kg_ha", "available_potassium_kg_ha", "soil_moisture_pct",
    "cumulative_rainfall_mm", "mean_temperature_c", "growing_degree_days",
    "relative_humidity_pct", "solar_radiation_mj_m2", "irrigation_area_fraction",
    "fertilizer_rate_kg_ha", "crop_type_encoded", "sowing_week", "harvest_week",
    "previous_season_yield_t_ha", "yield_3yr_moving_avg_t_ha",
]


@yield_bp.route("/predict", methods=["POST"])
@require_auth
@require_permission("yield.predict")
def predict():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    missing = [f for f in REQUIRED_FEATURES if f not in data.get("features", {})]
    if missing:
        return jsonify({"error": f"Missing features: {missing}"}), 400

    predictor = get_predictor()
    if predictor is None:
        return jsonify({"error": "Yield prediction model not loaded"}), 503

    try:
        result = predictor.predict(data["features"])
    except Exception as e:
        log_audit("yield_predict_error", 500, str(e))
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

    record = YieldPrediction(
        user_id=g.current_user.id,
        district=data.get("district", "Unknown"),
        state=data.get("state", ""),
        crop_type=data.get("crop_type", "Unknown"),
        season=data.get("season", ""),
        predicted_yield=result["predicted_yield_t_ha"],
        ci_lower=result["confidence_interval"]["lower"],
        ci_upper=result["confidence_interval"]["upper"],
        features_json=data["features"],
    )
    db.session.add(record)
    db.session.commit()

    log_audit("yield_predict_success", 200,
              f"{data.get('district')}: {result['predicted_yield_t_ha']} t/ha")

    return jsonify({
        "id": record.id,
        "predicted_yield_t_ha": result["predicted_yield_t_ha"],
        "confidence_interval": result["confidence_interval"],
        "feature_importances": result.get("feature_importances", []),
    })


@yield_bp.route("/analytics", methods=["GET"])
@require_auth
@require_permission("yield.analytics")
def analytics():
    predictions = YieldPrediction.query.order_by(YieldPrediction.timestamp.desc()).limit(100).all()

    if not predictions:
        return jsonify({
            "average_yield": 0, "total_predictions": 0,
            "predictions": [], "districts": [], "crops": [],
        })

    yields = [p.predicted_yield for p in predictions]
    districts = list(set(p.district for p in predictions))
    crops = list(set(p.crop_type for p in predictions))

    return jsonify({
        "average_yield": round(sum(yields) / len(yields), 2),
        "total_predictions": len(predictions),
        "min_yield": round(min(yields), 2),
        "max_yield": round(max(yields), 2),
        "predictions": [p.to_dict() for p in predictions[:20]],
        "districts": sorted(districts),
        "crops": sorted(crops),
    })


@yield_bp.route("/features", methods=["GET"])
@require_auth
@require_permission("yield.features")
def features():
    importance = [
        {"feature": "Previous season yield", "importance": 0.187},
        {"feature": "Cumulative rainfall", "importance": 0.143},
        {"feature": "Growing degree days", "importance": 0.112},
        {"feature": "Fertiliser application rate", "importance": 0.098},
        {"feature": "Available nitrogen", "importance": 0.084},
        {"feature": "Soil moisture", "importance": 0.072},
        {"feature": "3-year yield moving average", "importance": 0.068},
        {"feature": "Mean temperature", "importance": 0.061},
        {"feature": "Irrigation area fraction", "importance": 0.054},
        {"feature": "Available phosphorus", "importance": 0.043},
    ]
    return jsonify({"feature_importances": importance})
