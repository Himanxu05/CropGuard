"""Authentication routes: login, register, refresh, profile."""

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
import jwt
from app import db
from app.models.user import User
from app.config import Config
from app.middleware.rbac import require_auth, require_role
from app.middleware.audit import log_audit

auth_bp = Blueprint("auth", __name__)


def generate_tokens(user):
    access_payload = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "type": "access",
    }
    refresh_payload = {
        "user_id": user.id,
        "exp": datetime.utcnow() + timedelta(days=30),
        "type": "refresh",
    }
    access_token = jwt.encode(access_payload, Config.JWT_SECRET_KEY, algorithm="HS256")
    refresh_token = jwt.encode(refresh_payload, Config.JWT_SECRET_KEY, algorithm="HS256")
    return access_token, refresh_token


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        log_audit("login_failed", 400, "Missing credentials")
        return jsonify({"error": "Email and password required"}), 400

    user = User.query.filter_by(email=data["email"]).first()
    if not user or not user.check_password(data["password"]):
        log_audit("login_failed", 401, f"Invalid credentials for {data.get('email')}")
        return jsonify({"error": "Invalid email or password"}), 401

    if user.status != "active":
        log_audit("login_failed", 403, f"Inactive user {user.username}")
        return jsonify({"error": "Account is inactive"}), 403

    user.last_login = datetime.utcnow()
    db.session.commit()

    access_token, refresh_token = generate_tokens(user)

    g.current_user = user
    log_audit("login_success", 200)

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict(),
    })


@auth_bp.route("/register", methods=["POST"])
@require_auth
@require_role("admin")
def register():
    data = request.get_json()
    required = ["username", "email", "password", "role"]
    if not data or not all(data.get(f) for f in required):
        return jsonify({"error": "Missing required fields"}), 400

    if data["role"] not in User.VALID_ROLES:
        return jsonify({"error": f"Invalid role. Must be one of: {User.VALID_ROLES}"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 409
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already taken"}), 409

    user = User(username=data["username"], email=data["email"], role=data["role"])
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    log_audit("user_registered", 201, f"Created user {user.username} with role {user.role}")

    return jsonify({"message": "User created", "user": user.to_dict()}), 201


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    data = request.get_json()
    token = data.get("refresh_token") if data else None
    if not token:
        return jsonify({"error": "Refresh token required"}), 400

    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            return jsonify({"error": "Invalid token type"}), 401
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return jsonify({"error": "Invalid or expired refresh token"}), 401

    user = db.session.get(User, payload["user_id"])
    if not user or user.status != "active":
        return jsonify({"error": "User not found"}), 401

    access_token, refresh_token = generate_tokens(user)
    return jsonify({"access_token": access_token, "refresh_token": refresh_token})


@auth_bp.route("/me", methods=["GET"])
@require_auth
def me():
    return jsonify({"user": g.current_user.to_dict()})


@auth_bp.route("/setup", methods=["POST"])
def initial_setup():
    """Create initial admin user if no users exist."""
    if User.query.count() > 0:
        return jsonify({"error": "Setup already completed"}), 400

    data = request.get_json() or {}
    admin = User(
        username=data.get("username", "admin"),
        email=data.get("email", "admin@cropguard.ai"),
        role="admin",
    )
    admin.set_password(data.get("password", "admin123"))
    db.session.add(admin)

    farmer = User(username="farmer", email="farmer@cropguard.ai", role="farmer")
    farmer.set_password("farmer123")
    db.session.add(farmer)

    officer = User(username="officer", email="officer@cropguard.ai", role="officer")
    officer.set_password("officer123")
    db.session.add(officer)

    db.session.commit()
    return jsonify({"message": "Initial users created", "users": [
        admin.to_dict(), farmer.to_dict(), officer.to_dict()
    ]}), 201
