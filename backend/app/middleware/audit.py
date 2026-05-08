"""Audit logging middleware — logs every API request."""

from flask import request, g
from datetime import datetime
from app import db
from app.models.audit_log import AuditLog


def log_audit(action, status_code=200, details=None):
    """Log an API action to the audit trail."""
    user = getattr(g, "current_user", None)
    try:
        log = AuditLog(
            user_id=user.id if user else None,
            username=user.username if user else "anonymous",
            action=action,
            endpoint=request.path,
            method=request.method,
            status_code=status_code,
            ip_address=request.remote_addr,
            details=details,
            timestamp=datetime.utcnow(),
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()
