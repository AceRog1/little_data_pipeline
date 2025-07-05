import os
import argparse
import numpy as np
import torch
import json
from tqdm import trange
import joblib

from train_lstm import LSTMModel


def load_model(model_path, meta, hidden_size, dropout, stacked):
    device = torch.device("cpu")
    model = LSTMModel(
        input_size=meta["n_features"],
        hidden_size=hidden_size,
        horizon=meta["horizon"],
        dropout=dropout,
        stacked=stacked
    ).to(device)

    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict)
    model.eval()
    return model


def rolling_forecast(model, start_window, steps_ahead, scaler_mean, scaler_std):
    """
    Perform a rolling forecast given an initial window.
    """
    lookback = start_window.shape[0]
    n_features = start_window.shape[1]
    horizon = model.fc.out_features

    window = start_window.copy()
    predictions = []

    device = torch.device("cpu")

    num_iterations = steps_ahead // horizon
    if steps_ahead % horizon != 0:
        num_iterations += 1

    for _ in trange(num_iterations, desc="Rolling forecast steps"):
        input_tensor = torch.tensor(window, dtype=torch.float32).unsqueeze(0).to(device)
        with torch.no_grad():
            pred = model(input_tensor).cpu().numpy().squeeze(0)

        predictions.append(pred)

        # Create next window by rolling in predictions
        for step in pred:
            new_row = np.zeros((n_features,))
            new_row[0] = step  # predicted congestion_count
            new_row[1:] = window[-1, 1:]  # keep other features constant
            window = np.vstack([window[1:], new_row])

    predictions = np.concatenate(predictions)[:steps_ahead]
    predictions_rescaled = predictions * scaler_std + scaler_mean
    return predictions_rescaled


def main(args):
    print(f"📌 Rolling forecast started")
    
    # Load meta
    with open(args.meta_file) as f:
        meta = json.load(f)
    print(f"✅ Loaded meta: lookback={meta['lookback']}, n_features={meta['n_features']}, horizon={meta['horizon']}")

    # Load scaler.pkl
    scaler = joblib.load(args.scaler_file)
    scaler_mean = scaler.mean_[0]
    scaler_std = scaler.scale_[0]
    print(f"✅ Loaded scaler (mean={scaler_mean:.3f}, std={scaler_std:.3f})")

    # Load start window
    start_window = np.load(args.start_window)
    if start_window.shape != (meta["lookback"], meta["n_features"]):
        raise ValueError(f"❌ start_window shape mismatch: expected {(meta['lookback'], meta['n_features'])}, got {start_window.shape}")
    print(f"✅ Loaded start window shape: {start_window.shape}")

    # Load trained model
    model = load_model(
        args.model_path,
        meta,
        hidden_size=args.hidden_size,
        dropout=args.dropout,
        stacked=args.stacked
    )
    print(f"✅ Loaded model from {args.model_path}")

    # Perform rolling forecast
    predictions = rolling_forecast(
        model,
        start_window,
        steps_ahead=args.steps_ahead,
        scaler_mean=scaler_mean,
        scaler_std=scaler_std
    )
    print(f"✅ Finished rolling forecast with {len(predictions)} steps")

    # Save predictions
    os.makedirs(args.out_dir, exist_ok=True)
    out_path = os.path.join(args.out_dir, "rolling_predictions.npy")
    np.save(out_path, predictions)
    print(f"💾 Saved rolling predictions to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rolling Forecast with trained LSTM Model")
    parser.add_argument("--model_path", required=True, help="Path to trained model .pt")
    parser.add_argument("--meta_file", required=True, help="Path to meta.json")
    parser.add_argument("--start_window", required=True, help="NPY file with shape (lookback, n_features)")
    parser.add_argument("--scaler_file", required=True, help="Path to scaler.pkl")
    parser.add_argument("--out_dir", default="outputs", help="Folder to save predictions")
    parser.add_argument("--hidden_size", type=int, required=True)
    parser.add_argument("--dropout", type=float, required=True)
    parser.add_argument("--steps_ahead", type=int, default=30, help="Total future steps to predict")
    parser.add_argument("--stacked", action="store_true", help="Use stacked (2-layer) LSTM")
    args = parser.parse_args()

    main(args)
