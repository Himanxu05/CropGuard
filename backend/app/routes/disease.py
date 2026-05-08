"""Disease detection API routes."""

import os
import hashlib
import uuid
from io import BytesIO
from flask import Blueprint, request, jsonify, g, send_file, current_app
from PIL import Image
from app import db
from app.models.diagnosis import DiagnosisLog
from app.middleware.rbac import require_auth, require_permission
from app.middleware.audit import log_audit

disease_bp = Blueprint("disease", __name__)

_detector = None

TREATMENTS = {
    "Apple___Apple_scab": "Apply fungicides such as captan or myclobutanil. Remove fallen leaves to reduce inoculum.",
    "Apple___Black_rot": "Prune infected branches. Apply fungicides during bloom period.",
    "Apple___Cedar_apple_rust": "Apply protective fungicides. Remove nearby juniper hosts.",
    "Corn_(maize)___Common_rust_": "Apply foliar fungicides like strobilurin. Plant resistant hybrids.",
    "Corn_(maize)___Northern_Leaf_Blight": "Use resistant hybrids. Apply fungicides at tasseling.",
    "Grape___Black_rot": "Apply fungicides before bloom. Remove mummified berries.",
    "Potato___Early_blight": "Apply chlorothalonil or mancozeb. Rotate crops.",
    "Potato___Late_blight": "Apply metalaxyl-based fungicides. Destroy infected plants.",
    "Tomato___Early_blight": "Apply copper-based fungicides. Mulch to prevent soil splash.",
    "Tomato___Late_blight": "Apply mancozeb or chlorothalonil immediately. Remove infected plants.",
    "Tomato___Bacterial_spot": "Apply copper sprays. Use disease-free seed.",
    "Tomato___Leaf_Mold": "Improve ventilation. Apply chlorothalonil.",
    "Tomato___Septoria_leaf_spot": "Remove lower infected leaves. Apply fungicides.",
    "Tomato___Target_Spot": "Apply chlorothalonil. Improve air circulation.",
}
DEFAULT_TREATMENT = "Consult a local agricultural extension officer for specific treatment recommendations."


def get_detector():
    global _detector
    if _detector is None:
        import sys
        # backend/app/routes/disease.py → go 4 levels up to cropguard/
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))))
        sys.path.insert(0, os.path.join(project_root, "models", "disease_detection"))
        try:
            from inference import DiseaseDetector
            model_path = current_app.config.get("DISEASE_MODEL_PATH")
            _detector = DiseaseDetector(model_path=model_path)
        except Exception as e:
            current_app.logger.error(f"Failed to load disease model: {e}")
            return None
    return _detector


def get_severity(confidence):
    if confidence >= 0.95:
        return "High"
    elif confidence >= 0.80:
        return "Medium"
    elif confidence >= 0.60:
        return "Low"
    return "Uncertain"


@disease_bp.route("/predict", methods=["POST"])
@require_auth
@require_permission("disease.predict")
def predict():
    if "image" not in request.files:
        log_audit("disease_predict_failed", 400, "No image provided")
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    allowed = {".jpg", ".jpeg", ".png"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        log_audit("disease_predict_failed", 400, f"Invalid format: {ext}")
        return jsonify({"error": f"Invalid image format. Allowed: {allowed}"}), 400

    image_bytes = file.read()

    server_hash = hashlib.sha256(image_bytes).hexdigest()
    client_hash = request.form.get("image_hash")
    if client_hash and client_hash != server_hash:
        log_audit("integrity_check_failed", 400, f"Hash mismatch: {client_hash} != {server_hash}")
        return jsonify({"error": "SHA-256 integrity check failed"}), 400

    detector = get_detector()
    if detector is None:
        return jsonify({"error": "Disease detection model not loaded"}), 503

    try:
        result = detector.predict(image_bytes, return_gradcam=True)
    except Exception as e:
        log_audit("disease_predict_error", 500, str(e))
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

    gradcam_filename = None
    if "gradcam_overlay" in result:
        gradcam_dir = current_app.config.get("GRADCAM_FOLDER", "/tmp/cropguard_gradcam")
        gradcam_filename = f"{uuid.uuid4().hex}.png"
        gradcam_path = os.path.join(gradcam_dir, gradcam_filename)
        Image.fromarray(result["gradcam_overlay"]).save(gradcam_path)

    severity = get_severity(result["confidence"])
    pred_class = result["predicted_class"]
    treatment = TREATMENTS.get(pred_class, DEFAULT_TREATMENT)

    log_entry = DiagnosisLog(
        user_id=g.current_user.id,
        image_hash=server_hash,
        image_filename=file.filename,
        predicted_class=pred_class,
        confidence=result["confidence"],
        top3_predictions=result["top3_predictions"],
        gradcam_path=gradcam_filename,
        severity=severity,
        treatment=treatment,
    )
    db.session.add(log_entry)
    db.session.commit()

    log_audit("disease_predict_success", 200, f"{pred_class} ({result['confidence']:.2%})")

    return jsonify({
        "id": log_entry.id,
        "predicted_class": pred_class,
        "confidence": result["confidence"],
        "severity": severity,
        "treatment": treatment,
        "top3_predictions": result["top3_predictions"],
        "image_hash": server_hash,
        "gradcam_available": gradcam_filename is not None,
    })


@disease_bp.route("/history", methods=["GET"])
@require_auth
@require_permission("disease.history")
def history():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = DiagnosisLog.query.filter_by(user_id=g.current_user.id)
    query = query.order_by(DiagnosisLog.timestamp.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "diagnoses": [d.to_dict() for d in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page,
    })


@disease_bp.route("/gradcam/<int:diagnosis_id>", methods=["GET"])
@require_auth
@require_permission("disease.gradcam")
def get_gradcam(diagnosis_id):
    diag = DiagnosisLog.query.get_or_404(diagnosis_id)

    if diag.user_id != g.current_user.id and g.current_user.role != "admin":
        return jsonify({"error": "Access denied"}), 403

    if not diag.gradcam_path:
        return jsonify({"error": "Grad-CAM not available"}), 404

    gradcam_dir = current_app.config.get("GRADCAM_FOLDER", "/tmp/cropguard_gradcam")
    path = os.path.join(gradcam_dir, diag.gradcam_path)

    if not os.path.exists(path):
        return jsonify({"error": "Grad-CAM file not found"}), 404

    return send_file(path, mimetype="image/png")
