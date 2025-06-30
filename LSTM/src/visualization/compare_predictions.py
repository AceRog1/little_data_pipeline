import os
import numpy as np
import matplotlib.pyplot as plt

def plot_comparisons(runs_folder, output_path, num_points=100):
    plt.figure(figsize=(12, 7))

    for run_dir in os.listdir(runs_folder):
        run_path = os.path.join(runs_folder, run_dir)
        y_val_path = os.path.join(run_path, "y_val.npy")
        y_pred_path = os.path.join(run_path, "y_pred.npy")

        if os.path.exists(y_val_path) and os.path.exists(y_pred_path):
            y_val = np.load(y_val_path).flatten()[:num_points]
            y_pred = np.load(y_pred_path).flatten()[:num_points]

            plt.plot(y_val, label=f"{run_dir} - Real", linestyle="dashed", alpha=0.6)
            plt.plot(y_pred, label=f"{run_dir} - Predicción", alpha=0.8)

    plt.title("Comparación de Predicciones vs Reales en Distintas Runs")
    plt.xlabel("Tiempo (minutos)")
    plt.ylabel("Congestión")
    plt.legend(fontsize=8)
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    print(f"✅ Gráfico guardado en {output_path}")

if __name__ == "__main__":
    runs_dir = "artifacts"  
    output_path = "src/visualization/output/comparacion_runs.png"
    plot_comparisons(runs_dir, output_path)
