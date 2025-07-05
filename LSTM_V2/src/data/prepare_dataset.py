import os
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
import joblib
from sklearn.preprocessing import StandardScaler

def load_all_files(input_dir):
    """Carga todos los CSV o Parquet del directorio dado"""
    dfs = []
    files = [f for f in os.listdir(input_dir) if f.endswith((".csv", ".parquet"))]
    if not files:
        raise ValueError(f"No CSV or Parquet files found in {input_dir}")

    print(f"🗂️  Loading {len(files)} files from {input_dir}")
    for file in tqdm(files, desc="Reading files"):
        path = os.path.join(input_dir, file)
        if file.endswith(".csv"):
            df = pd.read_csv(path)
        else:
            df = pd.read_parquet(path)
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

def clean_data(df):
    """Limpieza básica de datos: nulos, formatos"""
    initial_len = len(df)
    df = df[df["on_ground"] == False]
    df = df.dropna(subset=["latitude", "longitude", "timestamp_ingest", "velocity"])
    df = df[df["velocity"] >= 0]
    df = df[df["latitude"].between(-90, 90)]
    df = df[df["longitude"].between(-180, 180)]
    print(f"✅ Cleaned data: {initial_len} → {len(df)} rows")
    return df

def assign_cells(df, cell_size_deg):
    """Asigna grid cell_id por lat/lon"""
    df["lat_bin"] = (df["latitude"] // cell_size_deg).astype(int)
    df["lon_bin"] = (df["longitude"] // cell_size_deg).astype(int)
    df["cell_id"] = df["lat_bin"].astype(str) + "_" + df["lon_bin"].astype(str)
    return df

def bin_time(df, time_bin):
    """Redondea timestamp a intervalos fijos"""
    before = len(df)
    df["timestamp_clean"] = df["timestamp_ingest"].str.replace("Z", "", regex=False)
    df["timestamp"] = pd.to_datetime(df["timestamp_clean"], utc=True, errors='coerce')
    df = df.dropna(subset=["timestamp"])
    after = len(df)
    print(f"✅ Valid timestamps: {after} / {before} rows")
    df["time_bin"] = df["timestamp"].dt.floor(time_bin)
    return df

def aggregate_features(df):
    """Agrega métricas por cell_id y time_bin"""
    agg = df.groupby(["cell_id", "time_bin"]).agg(
        congestion_count=("icao24", "nunique"),
        mean_velocity=("velocity", "mean"),
        std_velocity=("velocity", "std"),
        mean_altitude=("baro_altitude", "mean"),
        std_altitude=("baro_altitude", "std"),
        n_callsigns=("callsign", "nunique"),
    ).reset_index()

    # Features horarias
    agg["hour"] = agg["time_bin"].dt.hour + agg["time_bin"].dt.minute / 60
    agg["hour_sin"] = np.sin(2 * np.pi * agg["hour"] / 24)
    agg["hour_cos"] = np.cos(2 * np.pi * agg["hour"] / 24)

    # Reemplazar nulos de std por 0
    agg["std_velocity"] = agg["std_velocity"].fillna(0)
    agg["std_altitude"] = agg["std_altitude"].fillna(0)

    return agg

def save_outputs(df, out_dir, base_name):
    """Guarda DataFrame en Parquet y opcional CSV"""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    parquet_path = os.path.join(out_dir, f"{base_name}.parquet")
    csv_path = os.path.join(out_dir, f"{base_name}.csv")
    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)
    print(f"💾 Saved: {parquet_path}")
    print(f"💾 Saved: {csv_path}")

def main(args):
    print("📌 Starting dataset preparation")
    print(f"➡️  Input: {args.input_dir}")
    print(f"➡️  Output: {args.out_dir}")
    print(f"➡️  Cell size: {args.cell_size_deg} deg")
    print(f"➡️  Time bin: {args.time_bin}")

    raw = load_all_files(args.input_dir)
    print(f"✅ Loaded {len(raw)} rows total")

    clean = clean_data(raw)

    cells = assign_cells(clean, args.cell_size_deg)

    binned = bin_time(cells, args.time_bin)

    agg = aggregate_features(binned)
    print(f"✅ Aggregated to {len(agg)} rows (cell_id x time_bin)")

    scaler = StandardScaler()
    agg["congestion_count"] = scaler.fit_transform(agg[["congestion_count"]])
    print(f"✅ Scaled congestion_count (mean={scaler.mean_[0]:.3f}, std={scaler.scale_[0]:.3f})")

    scaler_path = os.path.join(args.out_dir, "scaler.pkl")
    joblib.dump(scaler, scaler_path)
    print(f"💾 Saved scaler to {scaler_path}")

    save_outputs(agg, args.out_dir, "aggregated_congestion")

    print("🎯 Dataset preparation complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare Air Traffic Congestion Dataset")
    parser.add_argument("--input_dir", default="data/raw", help="Input folder with CSV/Parquet files")
    parser.add_argument("--out_dir", default="data/processed", help="Output folder")
    parser.add_argument("--cell_size_deg", type=float, default=0.5, help="Grid cell size in degrees")
    parser.add_argument("--time_bin", default="1min", help="Time bin size (e.g., '1min', '5min')")
    args = parser.parse_args()
    main(args)
