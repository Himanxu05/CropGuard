"""Celery worker for async tasks."""

import os
from celery import Celery

celery_app = Celery(
    "cropguard",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)


@celery_app.task(bind=True, max_retries=3)
def predict_yield_async(self, features, metadata):
    """Async yield prediction task."""
    try:
        import sys
        model_dir = os.environ.get("YIELD_MODEL_DIR",
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "models", "yield_prediction"))
        sys.path.insert(0, model_dir)
        from inference import YieldPredictor
        predictor = YieldPredictor(model_dir=model_dir)
        result = predictor.predict(features)
        return {"status": "success", "result": result, "metadata": metadata}
    except Exception as exc:
        self.retry(exc=exc, countdown=5)


@celery_app.task
def log_model_retrain(model_type):
    """Placeholder for model retraining trigger."""
    return {"status": "triggered", "model": model_type}
