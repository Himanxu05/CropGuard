#!/usr/bin/env python3
"""Inference wrapper for disease detection model."""

import torch
import torch.nn.functional as F
import hashlib
import io
from pathlib import Path
from torchvision import transforms
from PIL import Image

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

MODEL_DIR = Path(__file__).parent


class DiseaseDetector:
    """Production inference wrapper for EfficientNet-B0 disease classifier."""

    def __init__(self, model_path=None, device=None):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        if model_path is None:
            model_path = MODEL_DIR / "best_model.pt"

        self.model_path = Path(model_path)
        self._load_model()

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])

    def _load_model(self):
        from train import build_model
        ckpt = torch.load(self.model_path, map_location=self.device, weights_only=False)
        self.num_classes = ckpt["num_classes"]
        self.class_names = ckpt["class_names"]
        self.model = build_model(self.num_classes)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.to(self.device).eval()

    @staticmethod
    def compute_sha256(image_bytes):
        return hashlib.sha256(image_bytes).hexdigest()

    @staticmethod
    def verify_integrity(image_bytes, expected_hash):
        actual = hashlib.sha256(image_bytes).hexdigest()
        return actual == expected_hash

    def predict(self, image_input, return_gradcam=True):
        """Run inference on a single image.

        Args:
            image_input: PIL Image, file path, or bytes
            return_gradcam: whether to generate Grad-CAM heatmap
        Returns:
            dict with prediction results
        """
        if isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input)).convert("RGB")
        elif isinstance(image_input, (str, Path)):
            img = Image.open(image_input).convert("RGB")
        else:
            img = image_input.convert("RGB")

        input_tensor = self.transform(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(input_tensor)
            probs = F.softmax(logits, dim=1).cpu().numpy()[0]

        pred_idx = int(probs.argmax())
        pred_name = self.class_names[pred_idx]
        confidence = float(probs[pred_idx])

        top3_idx = probs.argsort()[::-1][:3]
        top3 = [{"class": self.class_names[i], "confidence": float(probs[i])} for i in top3_idx]

        result = {
            "predicted_class": pred_name,
            "confidence": confidence,
            "top3_predictions": top3,
        }

        if return_gradcam:
            from gradcam import GradCAM, apply_heatmap
            import numpy as np
            gradcam = GradCAM(self.model)
            cam, _, _ = gradcam.generate(input_tensor.clone().requires_grad_(True), pred_idx)
            img_np = np.array(img.resize((224, 224)))
            overlay = apply_heatmap(img_np, cam)
            result["gradcam_heatmap"] = cam
            result["gradcam_overlay"] = overlay

        return result
