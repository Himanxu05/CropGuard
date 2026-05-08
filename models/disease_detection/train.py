#!/usr/bin/env python3
"""EfficientNet-B0 training pipeline for 38-class plant disease detection.

Hyperparameters match Table 7.2 from the capstone report:
- AdamW optimizer, LR=3e-4, weight_decay=1e-4
- Batch size 32, 30 epochs, cosine annealing (Tmax=30)
- Cross-entropy with label smoothing (0.1)
- Early stopping patience 5, dropout 0.3
- Input resolution 224x224, ImageNet pretrained
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from torch.optim.lr_scheduler import CosineAnnealingLR
import numpy as np

MODEL_DIR = Path(__file__).parent
DATASET_DIR = Path(__file__).parent.parent.parent / "datasets" / "plantvillage"

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def get_transforms():
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.5),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    
    return train_transform, val_transform


def build_model(num_classes, dropout=0.3):
    """Build EfficientNet-B0 with custom classifier head."""
    model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
    
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=dropout, inplace=True),
        nn.Linear(in_features, num_classes)
    )
    
    return model


def train_one_epoch(model, loader, criterion, optimizer, device, epoch):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for batch_idx, (images, labels) in enumerate(loader):
        images, labels = images.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
        
        if (batch_idx + 1) % 50 == 0:
            print(f"  Epoch {epoch} | Batch {batch_idx+1}/{len(loader)} | "
                  f"Loss: {loss.item():.4f} | Acc: {100.*correct/total:.1f}%")
    
    epoch_loss = running_loss / total
    epoch_acc = 100. * correct / total
    return epoch_loss, epoch_acc


def validate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            running_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
    
    epoch_loss = running_loss / total
    epoch_acc = 100. * correct / total
    return epoch_loss, epoch_acc


def main():
    parser = argparse.ArgumentParser(description="Train EfficientNet-B0 for disease detection")
    parser.add_argument("--data-dir", type=str, default=str(DATASET_DIR))
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--label-smoothing", type=float, default=0.1)
    parser.add_argument("--patience", type=int, default=5)
    parser.add_argument("--lightweight", action="store_true",
                        help="Quick training: 5 epochs, 10%% data")
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--output-dir", type=str, default=str(MODEL_DIR))
    args = parser.parse_args()
    
    if args.lightweight:
        args.epochs = 5
        args.batch_size = 16
        print("[INFO] Lightweight mode: 5 epochs, reduced data")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Using device: {device}")
    if device.type == "cuda":
        print(f"[INFO] GPU: {torch.cuda.get_device_name(0)}")
    
    train_transform, val_transform = get_transforms()
    
    data_dir = Path(args.data_dir)
    train_dir = data_dir / "train"
    val_dir = data_dir / "val"
    test_dir = data_dir / "test"
    
    if not train_dir.exists():
        print(f"[ERROR] Training data not found at {train_dir}")
        print("Run: python datasets/download_plantvillage.py first")
        sys.exit(1)
    
    train_dataset = datasets.ImageFolder(train_dir, transform=train_transform)
    val_dataset = datasets.ImageFolder(val_dir, transform=val_transform)
    
    if args.lightweight:
        n_train = len(train_dataset) // 10
        n_val = len(val_dataset) // 10
        train_dataset = torch.utils.data.Subset(train_dataset,
                                                 np.random.choice(len(train_dataset), n_train, replace=False))
        val_dataset = torch.utils.data.Subset(val_dataset,
                                               np.random.choice(len(val_dataset), n_val, replace=False))
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size,
                              shuffle=True, num_workers=args.num_workers, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size,
                            shuffle=False, num_workers=args.num_workers, pin_memory=True)
    
    num_classes = len(datasets.ImageFolder(train_dir).classes)
    class_names = datasets.ImageFolder(train_dir).classes
    print(f"[INFO] Dataset: {len(train_dataset)} train, {len(val_dataset)} val, {num_classes} classes")
    
    model = build_model(num_classes, dropout=args.dropout).to(device)
    print(f"[INFO] Model parameters: {sum(p.numel() for p in model.parameters()) / 1e6:.1f}M")
    
    criterion = nn.CrossEntropyLoss(label_smoothing=args.label_smoothing)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    best_val_acc = 0.0
    patience_counter = 0
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": [], "lr": []}
    
    start_time = time.time()
    
    for epoch in range(1, args.epochs + 1):
        print(f"\n{'='*60}")
        print(f"Epoch {epoch}/{args.epochs} | LR: {scheduler.get_last_lr()[0]:.6f}")
        print(f"{'='*60}")
        
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion,
                                                 optimizer, device, epoch)
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        
        scheduler.step()
        
        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        history["lr"].append(scheduler.get_last_lr()[0])
        
        print(f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
        print(f"  Val Loss:   {val_loss:.4f} | Val Acc:   {val_acc:.2f}%")
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_acc": val_acc,
                "val_loss": val_loss,
                "num_classes": num_classes,
                "class_names": class_names,
            }, output_dir / "best_model.pt")
            print(f"  *** New best model saved (val_acc={val_acc:.2f}%) ***")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"\n[INFO] Early stopping triggered at epoch {epoch}")
                break
    
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"Training complete in {elapsed/60:.1f} minutes")
    print(f"Best validation accuracy: {best_val_acc:.2f}%")
    
    with open(output_dir / "training_history.json", "w") as f:
        json.dump(history, f, indent=2)
    
    with open(output_dir / "class_names.json", "w") as f:
        json.dump(class_names, f, indent=2)
    
    config = {
        "model": "EfficientNet-B0",
        "num_classes": num_classes,
        "input_size": 224,
        "best_val_acc": best_val_acc,
        "epochs_trained": len(history["train_loss"]),
        "device": str(device),
        "training_time_minutes": round(elapsed / 60, 1),
    }
    with open(output_dir / "training_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"[SUCCESS] Model saved to {output_dir / 'best_model.pt'}")


if __name__ == "__main__":
    main()
