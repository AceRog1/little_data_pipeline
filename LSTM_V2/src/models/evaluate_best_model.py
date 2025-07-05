import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import argparse
import json
import os

class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size, horizon, dropout, stacked):
        super().__init__()
        if stacked:
            self.lstm = nn.LSTM(input_size, hidden_size, num_layers=2, dropout=dropout, batch_first=True)
        else:
            self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, horizon)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        out = self.dropout(out)
        out = self.fc(out)
        return out

def main(args):
    with open(os.path.join(args.windows_dir, "meta.json")) as f:
        meta = json.load(f)

    input_size = meta["n_features"]
    horizon = meta["horizon"]

    print(f"✅ Loaded meta: input_size={input_size}, horizon={horizon}")

    X_val = np.load(os.path.join(args.windows_dir, "X_val.npz"))['arr_0']
    y_val = np.load(os.path.join(args.windows_dir, "y_val.npz"))['arr_0']

    X_val_tensor = torch.tensor(X_val, dtype=torch.float32)
    y_val_tensor = torch.tensor(y_val, dtype=torch.float32)

    print(f"✅ Validation data: X_val {X_val.shape}, y_val {y_val.shape}")

    model = LSTMModel(
        input_size=input_size,
        hidden_size=args.hidden_size,
        horizon=horizon,
        dropout=args.dropout,
        stacked=args.stacked
    )
    model.load_state_dict(torch.load(args.model_path, map_location="cpu"))
    model.eval()

    print(f"✅ Loaded model from {args.model_path}")

    with torch.no_grad():
        preds = model(X_val_tensor).numpy()

    n_examples = min(100, len(y_val))
    plt.figure(figsize=(12, 6))
    plt.plot(y_val[:n_examples, 0], label="Real_t+1", color='blue')
    plt.plot(preds[:n_examples, 0], label="Pred_t+1", color='orange')
    plt.title("Pred vs Real (t+1)")
    plt.legend()
    plt.tight_layout()

    out_plot = os.path.join(args.out_dir, "prediction_vs_real_t+1.png")
    os.makedirs(args.out_dir, exist_ok=True)
    plt.savefig(out_plot)
    plt.close()
    print(f"✅ Saved plot: {out_plot}")

    np.savez_compressed(os.path.join(args.out_dir, "predictions.npz"), preds=preds, y_true=y_val)
    print(f"✅ Saved predictions and ground truth to {args.out_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate best LSTM model and plot predictions")
    parser.add_argument("--model_path", required=True, help="Path to best_model.pt")
    parser.add_argument("--windows_dir", default="data/processed/windows", help="Directory with windowed data")
    parser.add_argument("--out_dir", default="outputs", help="Where to save plots and results")
    parser.add_argument("--hidden_size", type=int, default=64)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--stacked", action="store_true", help="Use stacked LSTM if model was trained with it")
    args = parser.parse_args()
    main(args)
