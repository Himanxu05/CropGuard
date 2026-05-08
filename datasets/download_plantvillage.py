#!/usr/bin/env python3
"""Download and organize the PlantVillage dataset for 38-class disease detection."""

import os
import sys
import shutil
import zipfile
import tarfile
import random
import argparse
from pathlib import Path
from collections import defaultdict

DATASET_DIR = Path(__file__).parent / "plantvillage"
RAW_DIR = DATASET_DIR / "raw"

KAGGLE_DATASET = "emmarex/plantdisease"
GITHUB_MIRROR_URL = "https://github.com/spMohanty/PlantVillage-Dataset/archive/refs/heads/master.zip"
DIRECT_URLS = [
    "https://data.mendeley.com/public-files/datasets/tywbtsjrjv/files/d5652a28-c1d8-4b76-97f3-72fb80f94efc/file_downloaded",
]

EXPECTED_CLASSES = 38


def download_with_kaggle():
    """Try downloading via Kaggle API."""
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        print("[INFO] Downloading PlantVillage from Kaggle...")
        api.dataset_download_files(KAGGLE_DATASET, path=str(RAW_DIR), unzip=True)
        return True
    except Exception as e:
        print(f"[WARN] Kaggle download failed: {e}")
        return False


def download_with_url(url, dest):
    """Download a file from URL with progress."""
    import requests
    from tqdm import tqdm
    
    print(f"[INFO] Downloading from {url[:80]}...")
    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    
    with open(dest, "wb") as f, tqdm(total=total, unit="B", unit_scale=True) as pbar:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
            pbar.update(len(chunk))
    return True


def download_github_mirror():
    """Download from GitHub mirror."""
    zip_path = RAW_DIR / "plantvillage_github.zip"
    try:
        download_with_url(GITHUB_MIRROR_URL, zip_path)
        print("[INFO] Extracting GitHub mirror...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(RAW_DIR)
        zip_path.unlink()
        repo_dir = RAW_DIR / "PlantVillage-Dataset-master"
        if repo_dir.exists():
            color_dir = repo_dir / "raw" / "color"
            if color_dir.exists():
                return color_dir
            for sub in repo_dir.rglob("*"):
                if sub.is_dir() and len(list(sub.iterdir())) > 30:
                    return sub
        return None
    except Exception as e:
        print(f"[WARN] GitHub mirror download failed: {e}")
        return None


def find_image_root(search_dir):
    """Find the directory containing the 38 class subdirectories."""
    for root, dirs, files in os.walk(search_dir):
        if len(dirs) >= 30:
            img_count = 0
            for d in dirs[:3]:
                dpath = Path(root) / d
                img_count += len([f for f in os.listdir(dpath) 
                                 if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            if img_count > 10:
                return Path(root)
    return None


def create_splits(source_dir, train_ratio=0.80, val_ratio=0.101, seed=42):
    """Split dataset into train/val/test maintaining class balance."""
    random.seed(seed)
    
    classes = sorted([d for d in os.listdir(source_dir)
                      if os.path.isdir(os.path.join(source_dir, d))])
    
    print(f"[INFO] Found {len(classes)} classes")
    
    splits = {"train": DATASET_DIR / "train",
              "val": DATASET_DIR / "val",
              "test": DATASET_DIR / "test"}
    
    for split_dir in splits.values():
        split_dir.mkdir(parents=True, exist_ok=True)
    
    stats = defaultdict(lambda: defaultdict(int))
    
    for cls in classes:
        cls_dir = Path(source_dir) / cls
        images = [f for f in os.listdir(cls_dir)
                  if f.lower().endswith(('.jpg', '.jpeg', '.png', '.JPG'))]
        random.shuffle(images)
        
        n = len(images)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        
        split_assignments = {
            "train": images[:n_train],
            "val": images[n_train:n_train + n_val],
            "test": images[n_train + n_val:]
        }
        
        for split_name, split_images in split_assignments.items():
            dest = splits[split_name] / cls
            dest.mkdir(parents=True, exist_ok=True)
            for img in split_images:
                src = cls_dir / img
                dst = dest / img
                if not dst.exists():
                    shutil.copy2(src, dst)
            stats[split_name][cls] = len(split_images)
    
    total = sum(sum(v.values()) for v in stats.values())
    print(f"\n[INFO] Dataset split complete:")
    print(f"  Train: {sum(stats['train'].values())} images")
    print(f"  Val:   {sum(stats['val'].values())} images")
    print(f"  Test:  {sum(stats['test'].values())} images")
    print(f"  Total: {total} images")
    print(f"  Classes: {len(classes)}")
    
    return len(classes)


def generate_class_names_file(source_dir):
    """Save class names to a text file."""
    classes = sorted([d for d in os.listdir(source_dir)
                      if os.path.isdir(os.path.join(source_dir, d))])
    names_file = DATASET_DIR / "class_names.txt"
    with open(names_file, "w") as f:
        for cls in classes:
            f.write(cls + "\n")
    print(f"[INFO] Saved {len(classes)} class names to {names_file}")
    return classes


def main():
    parser = argparse.ArgumentParser(description="Download PlantVillage dataset")
    parser.add_argument("--skip-download", action="store_true",
                        help="Skip download, only reorganize existing data")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    
    if (DATASET_DIR / "train").exists() and len(list((DATASET_DIR / "train").iterdir())) >= 30:
        print("[INFO] Dataset already exists with splits. Skipping.")
        return
    
    source_dir = None
    
    if not args.skip_download:
        if download_with_kaggle():
            source_dir = find_image_root(RAW_DIR)
        
        if source_dir is None:
            source_dir = download_github_mirror()
        
        if source_dir is None:
            for url in DIRECT_URLS:
                try:
                    fname = RAW_DIR / "plantvillage_direct.zip"
                    download_with_url(url, fname)
                    with zipfile.ZipFile(fname, "r") as zf:
                        zf.extractall(RAW_DIR)
                    fname.unlink()
                    source_dir = find_image_root(RAW_DIR)
                    if source_dir:
                        break
                except Exception as e:
                    print(f"[WARN] Direct URL failed: {e}")
    else:
        source_dir = find_image_root(RAW_DIR)
    
    if source_dir is None:
        print("[ERROR] Could not download PlantVillage dataset automatically.")
        print("Please download manually from one of these sources:")
        print(f"  1. Kaggle: https://www.kaggle.com/datasets/{KAGGLE_DATASET}")
        print(f"  2. GitHub: {GITHUB_MIRROR_URL}")
        print(f"Then extract to: {RAW_DIR}")
        sys.exit(1)
    
    print(f"[INFO] Found image root at: {source_dir}")
    generate_class_names_file(source_dir)
    n_classes = create_splits(source_dir, seed=args.seed)
    
    if n_classes < EXPECTED_CLASSES:
        print(f"[WARN] Expected {EXPECTED_CLASSES} classes, found {n_classes}")
    else:
        print(f"[SUCCESS] PlantVillage dataset ready with {n_classes} classes!")


if __name__ == "__main__":
    main()
