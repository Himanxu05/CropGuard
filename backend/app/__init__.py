import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name=None):
    """Flask application factory."""
    app = Flask(__name__)

    if config_name is None:
        config_name = os.environ.get("FLASK_CONFIG", "development")

    from app.config import config_map
    app.config.from_object(config_map.get(config_name, config_map["default"]))

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    migrate.init_app(app, db)

    os.makedirs(app.config.get("UPLOAD_FOLDER", "/tmp/cropguard_uploads"), exist_ok=True)
    os.makedirs(app.config.get("GRADCAM_FOLDER", "/tmp/cropguard_gradcam"), exist_ok=True)

    from app.models.user import User
    from app.models.diagnosis import DiagnosisLog
    from app.models.yield_record import YieldPrediction
    from app.models.audit_log import AuditLog

    from app.routes.auth import auth_bp
    from app.routes.disease import disease_bp
    from app.routes.yield_pred import yield_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(disease_bp, url_prefix="/api/disease")
    app.register_blueprint(yield_bp, url_prefix="/api/yield")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    with app.app_context():
        db.create_all()

    @app.route("/api/health")
    def health():
        return {"status": "healthy", "service": "CropGuard AI API"}

    return app
