#!/usr/bin/env python3
"""Seed database with demo users and sample data."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import create_app, db
from app.models.user import User
from app.models.diagnosis import DiagnosisLog
from app.models.audit_log import AuditLog
from datetime import datetime, timedelta
import random


def seed():
    app = create_app('development')
    with app.app_context():
        db.create_all()

        if User.query.count() == 0:
            users = [
                ('admin', 'admin@cropguard.ai', 'admin123', 'admin'),
                ('farmer', 'farmer@cropguard.ai', 'farmer123', 'farmer'),
                ('officer', 'officer@cropguard.ai', 'officer123', 'officer'),
                ('ravi_kumar', 'ravi@cropguard.ai', 'pass123', 'farmer'),
                ('priya_sharma', 'priya@cropguard.ai', 'pass123', 'farmer'),
                ('district_officer', 'do@cropguard.ai', 'pass123', 'officer'),
            ]
            for uname, email, pwd, role in users:
                u = User(username=uname, email=email, role=role)
                u.set_password(pwd)
                db.session.add(u)
            db.session.commit()
            print(f"[INFO] Created {len(users)} users")

        farmer = User.query.filter_by(username='farmer').first()
        if farmer and DiagnosisLog.query.count() == 0:
            diseases = [
                ('Tomato___Late_blight', 0.983),
                ('Apple___Cedar_apple_rust', 0.967),
                ('Tomato___healthy', 0.991),
                ('Corn_(maize)___Common_rust_', 0.945),
                ('Potato___Early_blight', 0.912),
            ]
            for disease, conf in diseases:
                d = DiagnosisLog(
                    user_id=farmer.id,
                    image_hash='demo_' + disease[:10],
                    predicted_class=disease,
                    confidence=conf,
                    severity='High' if conf > 0.95 else 'Medium',
                    treatment='Apply recommended fungicide treatment.',
                    timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                )
                db.session.add(d)
            db.session.commit()
            print(f"[INFO] Created {len(diseases)} sample diagnoses")

        if AuditLog.query.count() == 0:
            actions = ['login_success', 'disease_predict_success', 'yield_predict_success',
                       'login_failed', 'user_registered']
            for i in range(20):
                a = AuditLog(
                    user_id=random.randint(1, 3),
                    username=random.choice(['admin', 'farmer', 'officer']),
                    action=random.choice(actions),
                    endpoint='/api/' + random.choice(['auth/login', 'disease/predict', 'yield/predict']),
                    method=random.choice(['GET', 'POST']),
                    status_code=random.choice([200, 200, 200, 401, 400]),
                    ip_address=f"192.168.1.{random.randint(1, 254)}",
                    timestamp=datetime.utcnow() - timedelta(hours=random.randint(0, 72)),
                )
                db.session.add(a)
            db.session.commit()
            print("[INFO] Created sample audit logs")

        print("[SUCCESS] Database seeded!")


if __name__ == '__main__':
    seed()
