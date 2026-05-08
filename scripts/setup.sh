#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "=========================================="
echo "  CropGuard AI - Setup Script"
echo "=========================================="

# 1. Python environment
echo ""
echo "[1/5] Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# 2. Datasets
echo ""
echo "[2/5] Downloading datasets..."
python datasets/download_plantvillage.py
python datasets/download_yield_data.py --force-synthetic

# 3. Frontend
echo ""
echo "[3/5] Setting up frontend..."
cd frontend
npm install
cd "$PROJECT_DIR"

# 4. Initialize database
echo ""
echo "[4/5] Initializing database..."
cd backend
FLASK_CONFIG=development python -c "
from app import create_app, db
app = create_app('development')
with app.app_context():
    db.create_all()
    print('[INFO] Database tables created')
"

# Setup initial users
python -c "
import requests
try:
    r = requests.post('http://localhost:5000/api/auth/setup', json={})
    print(f'[INFO] Setup: {r.json()}')
except:
    print('[INFO] Setup will be done when server starts')
"
cd "$PROJECT_DIR"

# 5. Summary
echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Train models:     bash scripts/train_all.sh"
echo "  2. Start backend:    cd backend && python wsgi.py"
echo "  3. Start frontend:   cd frontend && npm run dev"
echo "  4. Open browser:     http://localhost:3000"
echo ""
echo "Docker (production):"
echo "  cd docker && docker-compose up -d"
