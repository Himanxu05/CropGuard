#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

LIGHTWEIGHT=""
if [ "$1" == "--lightweight" ]; then
    LIGHTWEIGHT="--lightweight"
    echo "[INFO] Running in LIGHTWEIGHT mode (quick training)"
fi

echo "=========================================="
echo "  CropGuard AI - Model Training"
echo "=========================================="

# Activate venv if exists
if [ -d "venv" ]; then source venv/bin/activate; fi

# Check GPU
python -c "
import torch
if torch.cuda.is_available():
    print(f'[INFO] GPU detected: {torch.cuda.get_device_name(0)}')
    print(f'[INFO] VRAM: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB')
else:
    print('[INFO] No GPU detected - using CPU')
    print('[INFO] Consider using --lightweight flag for faster training')
"

# 1. Disease Detection Model
echo ""
echo "=== Training Disease Detection Model ==="
echo "Model: EfficientNet-B0 | Dataset: PlantVillage (38 classes)"
echo ""
cd models/disease_detection
python train.py $LIGHTWEIGHT
echo ""
echo "Running evaluation..."
python evaluate.py
cd "$PROJECT_DIR"

# 2. Yield Prediction Model
echo ""
echo "=== Training Yield Prediction Model ==="
echo "Model: XGBoost-LSTM Hybrid | Features: 18"
echo ""
cd models/yield_prediction
python train_hybrid.py $LIGHTWEIGHT
cd "$PROJECT_DIR"

echo ""
echo "=========================================="
echo "  Training Complete!"
echo "=========================================="
echo ""
echo "Model files:"
echo "  Disease: models/disease_detection/best_model.pt"
echo "  XGBoost: models/yield_prediction/xgboost_model.json"
echo "  LSTM:    models/yield_prediction/lstm_model.pt"
echo "  Scaler:  models/yield_prediction/scaler.pkl"
echo ""
echo "Evaluation artifacts:"
echo "  models/disease_detection/confusion_matrix.png"
echo "  models/disease_detection/training_curves.png"
echo "  models/disease_detection/model_comparison.png"
echo "  models/yield_prediction/yield_prediction_results.png"
echo "  models/yield_prediction/feature_importance.png"
