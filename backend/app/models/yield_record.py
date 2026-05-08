from datetime import datetime
from app import db


class YieldPrediction(db.Model):
    __tablename__ = "yield_predictions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=True)
    crop_type = db.Column(db.String(50), nullable=False)
    season = db.Column(db.String(20), nullable=True)
    predicted_yield = db.Column(db.Float, nullable=False)
    ci_lower = db.Column(db.Float, nullable=True)
    ci_upper = db.Column(db.Float, nullable=True)
    features_json = db.Column(db.JSON, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "district": self.district,
            "state": self.state,
            "crop_type": self.crop_type,
            "season": self.season,
            "predicted_yield": self.predicted_yield,
            "confidence_interval": {"lower": self.ci_lower, "upper": self.ci_upper},
            "features": self.features_json,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
