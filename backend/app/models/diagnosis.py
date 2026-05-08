from datetime import datetime
from app import db


class DiagnosisLog(db.Model):
    __tablename__ = "diagnosis_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    image_hash = db.Column(db.String(64), nullable=False)
    image_filename = db.Column(db.String(256), nullable=True)
    predicted_class = db.Column(db.String(100), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    top3_predictions = db.Column(db.JSON, nullable=True)
    gradcam_path = db.Column(db.String(512), nullable=True)
    severity = db.Column(db.String(20), nullable=True)
    treatment = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "image_hash": self.image_hash,
            "predicted_class": self.predicted_class,
            "confidence": self.confidence,
            "top3_predictions": self.top3_predictions,
            "gradcam_path": self.gradcam_path,
            "severity": self.severity,
            "treatment": self.treatment,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
