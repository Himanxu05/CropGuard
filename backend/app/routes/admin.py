"""Admin API routes: user management, audit logs, dashboard stats."""

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models.user import User
from app.models.diagnosis import DiagnosisLog
from app.models.yield_record import YieldPrediction
from app.models.audit_log import AuditLog
from app.middleware.rbac import require_auth, require_role
from app.middleware.audit import log_audit

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard", methods=["GET"])
@require_auth
@require_role("admin")
def dashboard():
    total_users = User.query.count()
    active_users = User.query.filter_by(status="active").count()

    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    api_calls_today = AuditLog.query.filter(AuditLog.timestamp >= today_start).count()
    diagnoses_today = DiagnosisLog.query.filter(DiagnosisLog.timestamp >= today_start).count()

    total_diagnoses = DiagnosisLog.query.count()
    total_yield_preds = YieldPrediction.query.count()

    recent = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()

    return jsonify({
        "total_users": total_users,
        "active_users": active_users,
        "models_deployed": 2,
        "api_calls_today": api_calls_today,
        "diagnoses_today": diagnoses_today,
        "total_diagnoses": total_diagnoses,
        "total_yield_predictions": total_yield_preds,
        "system_health": {
            "disease_detection_model": "operational",
            "yield_prediction_model": "operational",
            "database": "operational",
            "api_gateway": "operational",
        },
        "recent_activity": [a.to_dict() for a in recent],
    })


@admin_bp.route("/users", methods=["GET"])
@require_auth
@require_role("admin")
def list_users():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    role = request.args.get("role")
    status = request.args.get("status")
    search = request.args.get("search", "")

    query = User.query
    if role:
        query = query.filter_by(role=role)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "users": [u.to_dict() for u in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page,
    })


@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@require_auth
@require_role("admin")
def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if "role" in data and data["role"] in User.VALID_ROLES:
        user.role = data["role"]
    if "status" in data and data["status"] in ("active", "inactive"):
        user.status = data["status"]
    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]

    db.session.commit()
    log_audit("user_updated", 200, f"Updated user {user.username}")
    return jsonify({"message": "User updated", "user": user.to_dict()})


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@require_auth
@require_role("admin")
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    if user.id == g.current_user.id:
        return jsonify({"error": "Cannot deactivate yourself"}), 400

    user.status = "inactive"
    db.session.commit()
    log_audit("user_deactivated", 200, f"Deactivated user {user.username}")
    return jsonify({"message": f"User {user.username} deactivated"})


@admin_bp.route("/audit-logs", methods=["GET"])
@require_auth
@require_role("admin")
def audit_logs():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    action_filter = request.args.get("action")
    user_filter = request.args.get("user")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    query = AuditLog.query
    if action_filter:
        query = query.filter(AuditLog.action.ilike(f"%{action_filter}%"))
    if user_filter:
        query = query.filter(AuditLog.username.ilike(f"%{user_filter}%"))
    if date_from:
        query = query.filter(AuditLog.timestamp >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(AuditLog.timestamp <= datetime.fromisoformat(date_to))

    pagination = query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "logs": [l.to_dict() for l in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page,
    })
