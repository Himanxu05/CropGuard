#!/usr/bin/env python3
"""Grad-CAM implementation for EfficientNet-B0 disease detection."""

import torch
import torch.nn.functional as F
import numpy as np
import cv2
from pathlib import Path
from torchvision import transforms
from PIL import Image

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class GradCAM:
    """Grad-CAM: compute class-discriminative localization maps."""

    def __init__(self, model, target_layer=None):
        self.model = model
        self.model.eval()
        self.gradients = None
        self.activations = None

        if target_layer is None:
            target_layer = model.features[-1]

        target_layer.register_forward_hook(self._save_activation)
        target_layer.register_full_backward_hook(self._save_gradient)

    def _save_activation(self, module, input, output):
        self.activations = output.detach()

    def _save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate(self, input_tensor, target_class=None):
        output = self.model(input_tensor)

        if target_class is None:
            target_class = output.argmax(dim=1).item()

        self.model.zero_grad()
        one_hot = torch.zeros_like(output)
        one_hot[0, target_class] = 1.0
        output.backward(gradient=one_hot, retain_graph=True)

        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        cam = (weights * self.activations).sum(dim=1, keepdim=True)
        cam = F.relu(cam)
        cam = F.interpolate(cam, size=input_tensor.shape[2:], mode="bilinear", align_corners=False)
        cam = cam.squeeze().cpu().numpy()

        if cam.max() > 0:
            cam = (cam - cam.min()) / (cam.max() - cam.min())

        return cam, target_class, output


def apply_heatmap(image_np, cam, alpha=0.5):
    heatmap = cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET)
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
    if image_np.max() <= 1.0:
        image_np = (image_np * 255).astype(np.uint8)
    overlay = np.uint8(alpha * heatmap + (1 - alpha) * image_np)
    return overlay


def generate_gradcam_for_image(model, image_path, class_names, device, output_path=None):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])

    img = Image.open(image_path).convert("RGB")
    img_resized = img.resize((224, 224))
    img_np = np.array(img_resized)

    input_tensor = transform(img).unsqueeze(0).to(device)

    gradcam = GradCAM(model)
    cam, pred_class, logits = gradcam.generate(input_tensor)

    probs = F.softmax(logits, dim=1).detach().cpu().numpy()[0]
    pred_name = class_names[pred_class] if class_names else str(pred_class)
    confidence = probs[pred_class]

    overlay = apply_heatmap(img_np, cam)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        overlay_img = Image.fromarray(overlay)
        overlay_img.save(output_path)

    top3_idx = np.argsort(probs)[::-1][:3]
    top3 = [(class_names[i] if class_names else str(i), float(probs[i])) for i in top3_idx]

    return {
        "predicted_class": pred_name,
        "confidence": float(confidence),
        "top3_predictions": top3,
        "heatmap": cam,
        "overlay": overlay,
    }


if __name__ == "__main__":
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--model-path", default=str(Path(__file__).parent / "best_model.pt"))
    parser.add_argument("--output", default="gradcam_output.png")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(args.model_path, map_location=device, weights_only=False)

    from train import build_model
    model = build_model(ckpt["num_classes"])
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device).eval()

    result = generate_gradcam_for_image(model, args.image, ckpt["class_names"], device, args.output)
    print(f"Prediction: {result['predicted_class']} ({result['confidence']*100:.1f}%)")
    for name, prob in result["top3_predictions"]:
        print(f"  {name}: {prob*100:.1f}%")
