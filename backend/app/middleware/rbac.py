"""RBAC middleware matching Table 7.6 permission matrix."""

from functools import wraps
from flask import request, jsonify, g
import jwt
from datetime import datetime
from app.config import Config
from app.models.user import User

PERMISSIONS = {
    "farmer": {
        "disease.predict", "disease.history", "disease.gradcam",
        "auth.me", "auth.refresh",
    },
    "officer": {
        "disease.predict", "disease.history", "disease.gradcam",
        "yield.predict", "yield.analytics", "yield.features",
        "auth.me", "auth.refresh",
    },
    "admin": {
        "disease.predict", "disease.history", "disease.gradcam",
        "yield.predict", "yield.analytics", "yield.features",
        "admin.users", "admin.users.update", "admin.users.delete",
        "admin.audit_logs", "admin.dashboard", "admin.retrain",
        "auth.me", "auth.refresh", "auth.register",
    },
}


def decode_token(token):
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    """Verify JWT token and attach user to request context."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Authentication required"}), 401

        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        from app import db
        user = db.session.get(User, payload.get("user_id"))
        if not user or user.status != "active":
            return jsonify({"error": "User not found or inactive"}), 401

        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def require_role(*allowed_roles):
    """Check that the authenticated user has one of the allowed roles."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = getattr(g, "current_user", None)
            if not user:
                return jsonify({"error": "Authentication required"}), 401
            if user.role not in allowed_roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def require_permission(permission):
    """Check specific permission from the RBAC matrix."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = getattr(g, "current_user", None)
            if not user:
                return jsonify({"error": "Authentication required"}), 401
            user_perms = PERMISSIONS.get(user.role, set())
            if permission not in user_perms:
                return jsonify({"error": f"Permission denied: {permission}"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
