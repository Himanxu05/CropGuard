#!/usr/bin/env python3
"""Download or generate realistic agriculture yield prediction dataset.

Generates district-level agricultural data matching the report specification:
- 210 districts across 3 states
- 12 years (2012-2023)
- 18 engineered features per record
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

DATASET_DIR = Path(__file__).parent / "yield_data"
OUTPUT_FILE = DATASET_DIR / "yield_dataset.csv"

KAGGLE_DATASETS = [
    "patelris/crop-yield-prediction-dataset",
    "akshatgupta7/crop-yield-in-indian-states",
]

STATES = {
    "Punjab": {"districts": 23, "base_yield": 4.5, "rainfall_range": (400, 800)},
    "Uttar Pradesh": {"districts": 75, "base_yield": 3.2, "rainfall_range": (600, 1200)},
    "Maharashtra": {"districts": 36, "base_yield": 2.8, "rainfall_range": (500, 2500)},
    "Madhya Pradesh": {"districts": 52, "base_yield": 2.5, "rainfall_range": (800, 1600)},
    "Rajasthan": {"districts": 24, "base_yield": 1.8, "rainfall_range": (200, 600)},
}

CROPS = ["Rice", "Wheat", "Maize", "Sugarcane", "Cotton", "Soybean", "Groundnut", "Mustard"]

DISTRICT_NAMES = {
    "Punjab": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda", "Moga",
               "Sangrur", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Kapurthala",
               "Faridkot", "Muktsar", "Mansa", "Barnala", "Fatehgarh Sahib",
               "Rupnagar", "SAS Nagar", "Nawanshahr", "Pathankot", "Tarn Taran",
               "Fazilka", "SBS Nagar"],
    "Uttar Pradesh": [f"UP_District_{i+1}" for i in range(75)],
    "Maharashtra": [f"MH_District_{i+1}" for i in range(36)],
    "Madhya Pradesh": [f"MP_District_{i+1}" for i in range(52)],
    "Rajasthan": [f"RJ_District_{i+1}" for i in range(24)],
}

YEARS = list(range(2012, 2024))


def try_kaggle_download():
    """Attempt to download from Kaggle."""
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        for ds in KAGGLE_DATASETS:
            try:
                print(f"[INFO] Trying Kaggle dataset: {ds}")
                api.dataset_download_files(ds, path=str(DATASET_DIR), unzip=True)
                for f in DATASET_DIR.glob("*.csv"):
                    df = pd.read_csv(f)
                    if len(df) > 100 and any(col in df.columns.str.lower()
                                              for col in ["yield", "production"]):
                        print(f"[INFO] Found suitable Kaggle dataset: {f.name}")
                        return df
            except Exception as e:
                print(f"[WARN] Failed for {ds}: {e}")
    except Exception as e:
        print(f"[WARN] Kaggle API not available: {e}")
    return None


def generate_synthetic_dataset(seed=42):
    """Generate realistic synthetic agriculture dataset matching report spec."""
    np.random.seed(seed)
    
    records = []
    
    for state, config in STATES.items():
        districts = DISTRICT_NAMES[state][:config["districts"]]
        
        for district in districts:
            district_factor = np.random.uniform(0.8, 1.2)
            prev_yield = config["base_yield"] * district_factor + np.random.normal(0, 0.2)
            yield_history = []
            
            for year in YEARS:
                for crop in np.random.choice(CROPS, size=np.random.randint(1, 4), replace=False):
                    crop_factor = {
                        "Rice": 1.0, "Wheat": 0.95, "Maize": 0.85,
                        "Sugarcane": 1.8, "Cotton": 0.6, "Soybean": 0.7,
                        "Groundnut": 0.65, "Mustard": 0.55
                    }.get(crop, 0.8)
                    
                    soil_ph = np.clip(np.random.normal(6.8, 0.8), 4.5, 9.0)
                    organic_carbon = np.clip(np.random.normal(0.65, 0.25), 0.1, 2.0)
                    available_n = np.clip(np.random.normal(250, 80), 50, 600)
                    available_p = np.clip(np.random.normal(25, 12), 5, 80)
                    available_k = np.clip(np.random.normal(200, 70), 50, 500)
                    soil_moisture = np.clip(np.random.normal(35, 12), 10, 70)
                    
                    rain_low, rain_high = config["rainfall_range"]
                    cumulative_rainfall = np.clip(
                        np.random.normal((rain_low + rain_high) / 2, (rain_high - rain_low) / 4),
                        rain_low * 0.5, rain_high * 1.5
                    )
                    mean_temp = np.clip(np.random.normal(28, 4), 15, 40)
                    gdd = np.clip(cumulative_rainfall * 0.8 + mean_temp * 50 + np.random.normal(0, 200),
                                  500, 4000)
                    relative_humidity = np.clip(np.random.normal(65, 15), 20, 95)
                    solar_radiation = np.clip(np.random.normal(18, 4), 8, 30)
                    
                    irrigation_fraction = np.clip(np.random.beta(2, 3), 0, 1)
                    fertilizer_rate = np.clip(np.random.normal(180, 60), 20, 400)
                    
                    crop_encoded = CROPS.index(crop)
                    sowing_week = np.random.randint(1, 30)
                    harvest_week = sowing_week + np.random.randint(14, 26)
                    
                    yield_3yr_avg = np.mean(yield_history[-3:]) if len(yield_history) >= 3 else prev_yield
                    
                    base = config["base_yield"] * crop_factor * district_factor
                    
                    rain_effect = 0.3 * (cumulative_rainfall - rain_low) / (rain_high - rain_low + 1)
                    nutrient_effect = 0.15 * (available_n / 300 + available_p / 30 + available_k / 250) / 3
                    temp_effect = -0.1 * abs(mean_temp - 26) / 10
                    fert_effect = 0.1 * fertilizer_rate / 200
                    moisture_effect = 0.05 * soil_moisture / 40
                    temporal_effect = 0.2 * (prev_yield / config["base_yield"] - 1)
                    year_trend = 0.01 * (year - 2012)
                    
                    actual_yield = np.clip(
                        base * (1 + rain_effect + nutrient_effect + temp_effect +
                                fert_effect + moisture_effect + temporal_effect + year_trend)
                        + np.random.normal(0, 0.15),
                        0.3, 12.0
                    )
                    
                    records.append({
                        "state": state,
                        "district": district,
                        "year": year,
                        "crop": crop,
                        "soil_ph": round(soil_ph, 2),
                        "organic_carbon_pct": round(organic_carbon, 3),
                        "available_nitrogen_kg_ha": round(available_n, 1),
                        "available_phosphorus_kg_ha": round(available_p, 1),
                        "available_potassium_kg_ha": round(available_k, 1),
                        "soil_moisture_pct": round(soil_moisture, 1),
                        "cumulative_rainfall_mm": round(cumulative_rainfall, 1),
                        "mean_temperature_c": round(mean_temp, 1),
                        "growing_degree_days": round(gdd, 0),
                        "relative_humidity_pct": round(relative_humidity, 1),
                        "solar_radiation_mj_m2": round(solar_radiation, 1),
                        "irrigation_area_fraction": round(irrigation_fraction, 3),
                        "fertilizer_rate_kg_ha": round(fertilizer_rate, 1),
                        "crop_type_encoded": crop_encoded,
                        "sowing_week": sowing_week,
                        "harvest_week": harvest_week,
                        "previous_season_yield_t_ha": round(prev_yield, 2),
                        "yield_3yr_moving_avg_t_ha": round(yield_3yr_avg, 2),
                        "yield_t_ha": round(actual_yield, 2),
                    })
                    
                    prev_yield = actual_yield
                    yield_history.append(actual_yield)
    
    df = pd.DataFrame(records)
    return df


def main():
    parser = argparse.ArgumentParser(description="Download/generate yield dataset")
    parser.add_argument("--force-synthetic", action="store_true",
                        help="Skip Kaggle, generate synthetic data directly")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    
    if OUTPUT_FILE.exists():
        df = pd.read_csv(OUTPUT_FILE)
        print(f"[INFO] Dataset already exists: {len(df)} records, {df.columns.tolist()}")
        return
    
    df = None
    
    if not args.force_synthetic:
        df = try_kaggle_download()
    
    if df is None:
        print("[INFO] Generating synthetic agriculture dataset...")
        df = generate_synthetic_dataset(seed=args.seed)
    
    df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\n[SUCCESS] Yield dataset saved to {OUTPUT_FILE}")
    print(f"  Records: {len(df)}")
    print(f"  Features: {len(df.columns)}")
    print(f"  States: {df['state'].nunique()}")
    print(f"  Districts: {df['district'].nunique()}")
    print(f"  Years: {df['year'].min()}-{df['year'].max()}")
    print(f"  Crops: {df['crop'].nunique()}")
    print(f"  Yield range: {df['yield_t_ha'].min():.2f} - {df['yield_t_ha'].max():.2f} t/ha")
    print(f"\nFeature columns:")
    for col in df.columns:
        print(f"  - {col}: {df[col].dtype}")


if __name__ == "__main__":
    main()
