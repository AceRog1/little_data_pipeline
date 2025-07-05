import torch
import numpy as np
import argparse
import json
from src.models.train_lstm import LSTMModel

def main(args):
    # Cargar meta
    with open(args.meta_file) as f:
        meta = json.load(f)

    lookback = meta["lookback"]
    n_features = meta["n_features"]
    horizon = meta["horizon"]

    print(f"✅ Loaded meta: lookback={lookback}, n_features={n_features}, horizon={horizon}")

    # Cargar modelo
    model = LSTMModel(
        input_size=n_features,
        hidden_size=args.hidden_size,
        horizon=horizon,
        dropout=args.dropout,
        stacked=args.stacked
    )
    model.load_state_dict(torch.load(args.model_path, map_location="cpu"))
    model.eval()
    print(f"✅ Loaded model from {args.model_path}")

    # Cargar ventana nueva
    window = np.load(args.new_window)
    print(f"✅ Loaded new window shape: {window.shape}")

    # Predecir
    with torch.no_grad():
        input_tensor = torch.tensor(window, dtype=torch.float32).unsqueeze(0)  # batch_size=1
        pred = model(input_tensor).squeeze(0).numpy()

    print("✅ Prediction (next horizon steps):")
    print(pred)

    np.save(args.out_file, pred)
    print(f"✅ Saved prediction to {args.out_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", required=True)
    parser.add_argument("--meta_file", required=True)
    parser.add_argument("--new_window", required=True, help="NPY file with shape (lookback, n_features)")
    parser.add_argument("--out_file", default="outputs/new_prediction.npy")
    parser.add_argument("--hidden_size", type=int, required=True)
    parser.add_argument("--dropout", type=float, required=True)
    parser.add_argument("--stacked", action="store_true")
    args = parser.parse_args()
    main(args)
