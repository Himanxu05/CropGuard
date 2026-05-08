#  CropGuard AI

**AI-Powered Crop Disease Detection and Yield Prediction System**

A production-grade platform combining EfficientNet-B0 for 38-class plant disease classification (97.2% accuracy) with an XGBoost-LSTM hybrid for district-level crop yield forecasting (R² = 0.91).

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│  React 18 +     │────▶│  Flask REST API  │────▶│ PostgreSQL   │
│  TailwindCSS    │     │  + Celery/Redis  │     │              │
│  (Port 3000)    │◀────│  (Port 5000)     │◀────│ (Port 5432)  │
└─────────────────┘     └────────┬────────-┘     └──────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
              ┌─────▼─────┐ ┌───▼──────┐ ┌──▼───────┐
              │EfficientNet│ │XGBoost-  │ │ Security │
              │   -B0      │ │  LSTM    │ │  Module  │
              │(Disease)   │ │ (Yield)  │ │(JWT/RBAC)│
              └────────────┘ └──────────┘ └──────────┘
```

##  Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) NVIDIA GPU with CUDA for full training

### 1. Setup
```bash
cd cropguard
chmod +x scripts/*.sh
bash scripts/setup.sh
```

### 2. Generate Yield Dataset
```bash
python datasets/download_yield_data.py --force-synthetic
```

### 3. Download PlantVillage Dataset
```bash
python datasets/download_plantvillage.py
```

If Kaggle API is not configured, download manually:
- https://www.kaggle.com/datasets/emmarex/plantdisease
- Extract to `datasets/plantvillage/raw/`

### 4. Train Models
```bash
# Full training (GPU recommended, ~3 hours)
bash scripts/train_all.sh

# Lightweight training (CPU-friendly, ~30 min)
bash scripts/train_all.sh --lightweight
```

### 5. Seed Database
```bash
python scripts/seed_db.py
```

### 6. Run Application
```bash
# Terminal 1: Backend
cd backend && python wsgi.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

Open http://localhost:3000

### 7. Docker (Production)
```bash
cd docker
docker-compose up -d
```

##  Project Structure

```
cropguard/
├── frontend/                 # React 18 + TailwindCSS
│   ├── src/
│   │   ├── components/       # Sidebar, reusable components
│   │   ├── pages/            # Login, Dashboard, DiseaseDetection, etc.
│   │   ├── services/         # API client with JWT interceptors
│   │   └── context/          # Auth context provider
│   ├── Dockerfile
│   └── package.json
├── backend/                  # Flask REST API
│   ├── app/
│   │   ├── models/           # SQLAlchemy: User, Diagnosis, Yield, AuditLog
│   │   ├── routes/           # auth, disease, yield, admin
│   │   ├── middleware/       # RBAC, audit logging
│   │   └── ml/               # Model inference wrappers
│   ├── celery_worker.py      # Async task queue
│   ├── Dockerfile
│   └── requirements.txt
├── models/
│   ├── disease_detection/    # EfficientNet-B0 pipeline
│   │   ├── train.py          # Training with all report hyperparameters
│   │   ├── evaluate.py       # Confusion matrix, metrics
│   │   ├── gradcam.py        # Grad-CAM heatmap generation
│   │   ├── adversarial.py    # FGSM robustness evaluation
│   │   └── inference.py      # Production wrapper
│   └── yield_prediction/     # XGBoost-LSTM hybrid
│       ├── train_hybrid.py   # Two-stage hybrid pipeline
│       └── inference.py      # Production wrapper
├── datasets/
│   ├── download_plantvillage.py
│   └── download_yield_data.py
├── docker/
│   ├── docker-compose.yml
│   └── nginx/nginx.conf
└── scripts/
    ├── setup.sh
    ├── train_all.sh
    └── seed_db.py
```

##  Demo Accounts

| Role    | Email                  | Password   | Access                          |
|---------|------------------------|------------|----------------------------------|
| Farmer  | farmer@cropguard.ai    | farmer123  | Disease detection only           |
| Officer | officer@cropguard.ai   | officer123 | Disease + Yield prediction       |
| Admin   | admin@cropguard.ai     | admin123   | Full access + user management    |

##  ML Models

### Disease Detection (EfficientNet-B0)
- **Dataset**: PlantVillage — 47,500 images, 38 classes
- **Accuracy**: 97.2% | Precision: 96.4% | Recall: 95.8% | F1: 96.1%
- **Training**: AdamW, LR=3e-4, cosine annealing, label smoothing=0.1
- **Explainability**: Grad-CAM heatmaps on every prediction
- **Adversarial**: FGSM evaluation at ε={0.01, 0.02, 0.03}

### Yield Prediction (XGBoost-LSTM Hybrid)
- **Dataset**: 210 districts, 12 years, 18 features
- **RMSE**: 0.31 t/ha | MAE: 0.22 t/ha | R²: 0.91
- **Architecture**: XGBoost feature transformation → LSTM temporal modeling

##  Security Features
- JWT authentication with access/refresh tokens
- bcrypt password hashing
- SHA-256 image integrity verification
- Role-Based Access Control (3 roles)
- Rate limiting (60 req/min per user)
- Audit logging on all API requests
- TLS-ready Nginx configuration
- Security headers (XSS, CSRF, CSP)

##  Estimated Training Time

| Model              | GPU (T4)   | CPU        |
|-------------------|------------|------------|
| EfficientNet-B0   | 2-3 hours  | 8-12 hours |
| Lightweight mode  | 15-20 min  | 30-45 min  |
| XGBoost-LSTM      | 10-15 min  | 15-30 min  |

##  API Endpoints

| Method | Endpoint              | Auth   | Description                |
|--------|-----------------------|--------|----------------------------|
| POST   | /api/auth/login       | No     | JWT login                  |
| POST   | /api/auth/register    | Admin  | Register new user          |
| GET    | /api/auth/me          | Yes    | Current user profile       |
| POST   | /api/disease/predict  | Yes    | Upload image, get diagnosis|
| GET    | /api/disease/history  | Yes    | Diagnosis history          |
| GET    | /api/disease/gradcam/:id | Yes | Get Grad-CAM overlay      |
| POST   | /api/yield/predict    | Officer| Yield prediction           |
| GET    | /api/yield/analytics  | Officer| District analytics         |
| GET    | /api/admin/dashboard  | Admin  | System stats               |
| GET    | /api/admin/users      | Admin  | User management            |
| GET    | /api/admin/audit-logs | Admin  | Audit trail                |
