import os
import matplotlib.pyplot as plt
import numpy as np

def plot_results(true_values, predictions, save_path=None):
    plt.figure(figsize=(10, 6))
    plt.plot(true_values, label="Real")
    plt.plot(predictions, label="Predicción")
    plt.title("Predicción de Congestión Aérea")
    plt.xlabel("Tiempo (minutos)")
    plt.ylabel("Congestión")
    plt.legend()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)  
        plt.savefig(save_path)
    else:
        plt.show()

if __name__ == "__main__":
    true_values = np.random.rand(100)
    predictions = np.random.rand(100)
    
    save_path = "src/visualization/output/prediction_vs_real.png"
    plot_results(true_values, predictions, save_path)
