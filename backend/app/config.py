import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "cropguard-dev-secret-key-change-in-prod")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "cropguard-jwt-secret-change-in-prod")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://cropguard:cropguard@localhost:5432/cropguard"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "/tmp/cropguard_uploads")
    GRADCAM_FOLDER = os.environ.get("GRADCAM_FOLDER", "/tmp/cropguard_gradcam")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

    RATE_LIMIT_DEFAULT = "60/minute"

    # __file__ = backend/app/config.py → go up 3 levels to project root (cropguard/)
    _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    DISEASE_MODEL_PATH = os.environ.get(
        "DISEASE_MODEL_PATH",
        os.path.join(_PROJECT_ROOT, "models", "disease_detection", "best_model.pt")
    )
    YIELD_MODEL_DIR = os.environ.get(
        "YIELD_MODEL_DIR",
        os.path.join(_PROJECT_ROOT, "models", "yield_prediction")
    )


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///cropguard_dev.db"
    )


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
