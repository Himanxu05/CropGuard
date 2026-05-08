#!/usr/bin/env python3
"""FGSM adversarial robustness evaluation for EfficientNet-B0."""

import torch
import torch.nn.functional as F
import json
import argparse
from pathlib import Path
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import numpy as np

MODEL_DIR = Path(__file__).parent
DATASET_DIR = Path(__file__).parent.parent.parent / "datasets" / "plantvillage"
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def fgsm_attack(model, images, labels, epsilon, criterion):
    """Generate FGSM adversarial examples: x_adv = x + eps * sign(grad_x L)."""
    images.requires_grad = True
    outputs = model(images)
    loss = criterion(outputs, labels)
    model.zero_grad()
    loss.backward()
    perturbed = images + epsilon * images.grad.sign()
    perturbed = torch.clamp(perturbed, 0, 1)
    return perturbed


def evaluate_adversarial(model, loader, epsilon, device):
    """Evaluate model accuracy under FGSM attack at given epsilon."""
    model.eval()
    criterion = torch.nn.CrossEntropyLoss()
    correct = 0
    total = 0
    denorm = transforms.Normalize(
        mean=[-m/s for m, s in zip(IMAGENET_MEAN, IMAGENET_STD)],
        std=[1/s for s in IMAGENET_STD]
    )
    renorm = transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        if epsilon > 0:
            images_denorm = torch.stack([denorm(img) for img in images])
            images_denorm = torch.clamp(images_denorm, 0, 1)
            perturbed = fgsm_attack(model, images_denorm.clone(), labels, epsilon, criterion)
            perturbed_norm = torch.stack([renorm(img) for img in perturbed])
            with torch.no_grad():
                outputs = model(perturbed_norm)
        else:
            with torch.no_grad():
                outputs = model(images)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    return correct / total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", default=str(MODEL_DIR / "best_model.pt"))
    parser.add_argument("--data-dir", default=str(DATASET_DIR))
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--epsilons", nargs="+", type=float, default=[0.0, 0.01, 0.02, 0.03])
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(args.model_path, map_location=device, weights_only=False)

    from train import build_model
    model = build_model(ckpt["num_classes"])
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device)

    tfm = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(),
                                transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)])
    test_dir = Path(args.data_dir) / "test"
    ds = datasets.ImageFolder(test_dir, transform=tfm)
    subset = torch.utils.data.Subset(ds, np.random.choice(len(ds), min(500, len(ds)), replace=False))
    dl = DataLoader(subset, batch_size=args.batch_size, shuffle=False, num_workers=2)

    results = []
    clean_acc = None
    for eps in args.epsilons:
        acc = evaluate_adversarial(model, dl, eps, device)
        if eps == 0.0:
            clean_acc = acc
        retention = acc / clean_acc if clean_acc else 1.0
        results.append({"epsilon": eps, "accuracy": round(acc * 100, 1),
                        "retention_ratio": round(retention, 3)})
        print(f"ε={eps:.2f} | Accuracy: {acc*100:.1f}% | Retention: {retention:.3f}")

    json.dump(results, open(MODEL_DIR / "adversarial_results.json", "w"), indent=2)
    print(f"\nResults saved to {MODEL_DIR / 'adversarial_results.json'}")


if __name__ == "__main__":
    main()
