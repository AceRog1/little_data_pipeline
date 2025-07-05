import os
import argparse
import pandas as pd
import numpy as np
from tqdm import tqdm
import json
from pathlib import Path
import shutil

def make_windows_for_cell(df_cell, lookback, horizon, feature_cols, target_col):
    df_cell = df_cell.sort_values("time_bin")
    data = df_cell[feature_cols + [target_col]].values
    X_cell, y_cell = [], []

    for i in range(len(data) - lookback - horizon + 1):
        x_window = data[i : i + lookback, :-1]
        y_window = data[i + lookback : i + lookback + horizon, -1]
        X_cell.append(x_window)
        y_cell.append(y_window)
    return np.array(X_cell), np.array(y_cell)

def main(args):
    print(f"📌 Creating windows from {args.input_file}")
    df = pd.read_parquet(args.input_file)
    print(f"✅ Loaded {len(df)} rows")

    all_columns = df.columns.tolist()
    print(f"➡️  Columns available: {all_columns}")

    features_cols = args.features_columns.split(",")
    target_col = args.target_column
    print(f"✅ Using features: {features_cols}")
    print(f"✅ Target: {target_col}")

    Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    X_list, y_list = [], []
    cell_ids = df["cell_id"].unique()
    print(f"➡️  Found {len(cell_ids)} unique cells")

    for cell in tqdm(cell_ids, desc="Processing cells"):
        df_cell = df[df["cell_id"] == cell].copy()
        df_cell = df_cell.sort_values("time_bin").reset_index(drop=True)
        df_cell = df_cell.dropna(subset=features_cols + [target_col])
        if len(df_cell) < args.lookback + args.horizon:
            continue

        X_cell, y_cell = make_windows_for_cell(
            df_cell, args.lookback, args.horizon, features_cols, target_col
        )
        if len(X_cell) == 0:
            continue

        X_list.append(X_cell)
        y_list.append(y_cell)

    X_all = np.vstack(X_list)
    y_all = np.vstack(y_list)
    print(f"✅ Total samples: {X_all.shape[0]}")
    print(f"✅ X shape: {X_all.shape}, y shape: {y_all.shape}")

    n_samples = X_all.shape[0]
    n_train = int(n_samples * (1 - args.test_frac))
    X_train, X_val = X_all[:n_train], X_all[n_train:]
    y_train, y_val = y_all[:n_train], y_all[n_train:]

    np.savez_compressed(os.path.join(args.out_dir, "X_train.npz"), X_train)
    np.savez_compressed(os.path.join(args.out_dir, "y_train.npz"), y_train)
    np.savez_compressed(os.path.join(args.out_dir, "X_val.npz"), X_val)
    np.savez_compressed(os.path.join(args.out_dir, "y_val.npz"), y_val)

    meta = {
        "lookback": args.lookback,
        "horizon": args.horizon,
        "n_features": X_train.shape[2],
        "features_used": features_cols,
        "target_column": target_col
    }
    with open(os.path.join(args.out_dir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    if args.scaler_file:
        print(f"✅ Copying scaler from {args.scaler_file}")
        shutil.copy(args.scaler_file, os.path.join(args.out_dir, "scaler.pkl"))

    print(f"✅ Saved all datasets and meta to {args.out_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create LSTM windows from aggregated congestion data")
    parser.add_argument("--input_file", default="data/processed/aggregated_congestion.parquet")
    parser.add_argument("--out_dir", default="data/processed/windows")
    parser.add_argument("--lookback", type=int, default=6)
    parser.add_argument("--horizon", type=int, default=3)
    parser.add_argument("--test_frac", type=float, default=0.2)
    parser.add_argument("--features_columns", default="congestion_count,mean_velocity,mean_altitude,hour_sin,hour_cos")
    parser.add_argument("--target_column", default="congestion_count")
    parser.add_argument("--scaler_file", default="data/processed/scaler.pkl", help="Path to the scaler to copy")
    args = parser.parse_args()
    main(args)
