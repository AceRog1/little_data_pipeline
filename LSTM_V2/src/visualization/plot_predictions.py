import numpy as np
import matplotlib.pyplot as plt
import argparse
import os

def plot_predictions(y_true, y_pred, out_dir, horizon):
    for i in range(horizon):
        plt.figure(figsize=(10, 6))
        plt.plot(y_true[:, i], label=f"Real t+{i+1}")
        plt.plot(y_pred[:, i], label=f"Predicho t+{i+1}")
        plt.title(f"Predicción vs Real para t+{i+1}")
        plt.xlabel("Muestras")
        plt.ylabel("Congestión (escalada)")
        plt.legend()
        plt.tight_layout()

        out_path = os.path.join(out_dir, f"prediction_vs_real_t+{i+1}.png")
        plt.savefig(out_path)
        plt.close()
        print(f"✅ Saved plot: {out_path}")

def main(args):
    y_true = np.load(os.path.join(args.run_folder, "y_val.npy"))
    y_pred = np.load(os.path.join(args.run_folder, "y_pred.npy"))
    horizon = y_true.shape[1]

    os.makedirs(args.out_dir, exist_ok=True)
    plot_predictions(y_true, y_pred, args.out_dir, horizon)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_folder", required=True, help="Folder with y_val.npy and y_pred.npy")
    parser.add_argument("--out_dir", default="outputs", help="Output directory for plots")
    args = parser.parse_args()
    main(args)
