import os
import subprocess
import itertools
import sys

def main():
    hidden_sizes = [32, 64]
    dropouts = [0.2, 0.4]
    learning_rates = [1e-3, 5e-4]
    stacked_options = [False, True]
    batch_size = 32
    epochs = 50
    patience = 10

    windows_dir = "data/processed/windows"
    out_dir = "artifacts"
    mlflow_uri = "file:./mlruns"
    experiment = "air_traffic_congestion"

    grid = list(itertools.product(hidden_sizes, dropouts, learning_rates, stacked_options))
    print(f"🧪 Total combinations: {len(grid)}")

    for i, (hidden_size, dropout, lr, stacked) in enumerate(grid, 1):
        run_name = f"grid_run_{i:02d}_hs{hidden_size}_do{dropout}_lr{lr}_stacked{stacked}"

        print(f"\n➡️  Launching run {i}/{len(grid)}: {run_name}")

        cmd = [
            sys.executable, "src/models/train_lstm.py",
            "--windows_dir", windows_dir,
            "--out_dir", out_dir,
            "--mlflow_uri", mlflow_uri,
            "--experiment", experiment,
            "--run_name", run_name,
            "--epochs", str(epochs),
            "--batch_size", str(batch_size),
            "--hidden_size", str(hidden_size),
            "--dropout", str(dropout),
            "--lr", str(lr),
            "--patience", str(patience),
        ]

        if stacked:
            cmd.append("--stacked")

        print(f"📜 Command: {' '.join(cmd)}")
        subprocess.run(cmd)

    print("\n✅ All grid runs completed!")

if __name__ == "__main__":
    main()
