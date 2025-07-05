import os
import argparse
import numpy as np
import matplotlib.pyplot as plt

def main(args):
    os.makedirs(args.out_dir, exist_ok=True)
    
    # Cargar predicciones
    preds = np.load(args.input_file)
    print(f"✅ Loaded predictions with shape: {preds.shape}")

    steps = np.arange(1, len(preds) + 1)

    # Umbral simple para definir "picos de congestión"
    threshold = args.threshold
    peaks = preds >= threshold

    print(f"➡️  Threshold for peaks: {threshold}")
    print(f"➡️  Detected {np.sum(peaks)} peaks")

    # Graficar
    plt.figure(figsize=(10, 6))
    plt.plot(steps, preds, label="Predicted congestion count", color="blue")
    plt.scatter(steps[peaks], preds[peaks], color="red", label="Detected peaks")
    plt.axhline(threshold, color="gray", linestyle="--", label=f"Threshold = {threshold}")
    plt.title("Rolling Forecast: Predicted Air Traffic Congestion")
    plt.xlabel("Future Time Step")
    plt.ylabel("Congestion Count (predicted)")
    plt.legend()
    plt.grid(alpha=0.3)

    # Guardar gráfico
    out_path = os.path.join(args.out_dir, "rolling_forecast_plot.png")
    plt.savefig(out_path)
    plt.close()
    print(f"✅ Saved plot to {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot rolling forecast predictions with congestion peaks highlighted")
    parser.add_argument("--input_file", required=True, help="Path to rolling_predictions.npy")
    parser.add_argument("--out_dir", default="outputs", help="Folder to save plot")
    parser.add_argument("--threshold", type=float, default=3.0, help="Threshold for defining congestion peaks")
    args = parser.parse_args()

    main(args)
