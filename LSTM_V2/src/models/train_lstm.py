import os
import argparse
import json
import numpy as np
import mlflow
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from tqdm import tqdm
import joblib

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

def load_data(windows_dir):
    X_train = np.load(os.path.join(windows_dir, "X_train.npz"))['arr_0']
    y_train = np.load(os.path.join(windows_dir, "y_train.npz"))['arr_0']
    X_val = np.load(os.path.join(windows_dir, "X_val.npz"))['arr_0']
    y_val = np.load(os.path.join(windows_dir, "y_val.npz"))['arr_0']
    with open(os.path.join(windows_dir, "meta.json")) as f:
        meta = json.load(f)
    scaler = joblib.load(os.path.join(windows_dir, "scaler.pkl"))
    return X_train, y_train, X_val, y_val, meta, scaler

def train_one_epoch(model, dataloader, loss_fn, optimizer, device):
    model.train()
    total_loss = 0
    total_mae = 0
    for X_batch, y_batch in dataloader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        optimizer.zero_grad()
        y_pred = model(X_batch)
        loss = loss_fn(y_pred, y_batch)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * X_batch.size(0)
        total_mae += torch.mean(torch.abs(y_pred - y_batch)).item() * X_batch.size(0)
    return total_loss / len(dataloader.dataset), total_mae / len(dataloader.dataset)

def validate(model, dataloader, loss_fn, device):
    model.eval()
    total_loss = 0
    total_mae = 0
    all_preds = []
    with torch.no_grad():
        for X_batch, y_batch in dataloader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            y_pred = model(X_batch)
            loss = loss_fn(y_pred, y_batch)
            total_loss += loss.item() * X_batch.size(0)
            total_mae += torch.mean(torch.abs(y_pred - y_batch)).item() * X_batch.size(0)
            all_preds.append(y_pred.cpu().numpy())
    return total_loss / len(dataloader.dataset), total_mae / len(dataloader.dataset), np.concatenate(all_preds)

def main(args):
    mlflow.set_tracking_uri(args.mlflow_uri)
    mlflow.set_experiment(args.experiment)
    with mlflow.start_run(run_name=args.run_name):
        mlflow.log_params(vars(args))

        X_train, y_train, X_val, y_val, meta, scaler = load_data(args.windows_dir)
        print(f"✅ Loaded data: X_train {X_train.shape}, y_train {y_train.shape}")

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {device}")

        train_ds = TensorDataset(torch.tensor(X_train, dtype=torch.float32),
                                 torch.tensor(y_train, dtype=torch.float32))
        val_ds = TensorDataset(torch.tensor(X_val, dtype=torch.float32),
                               torch.tensor(y_val, dtype=torch.float32))

        train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False)

        model = LSTMModel(
            input_size=meta["n_features"],
            hidden_size=args.hidden_size,
            horizon=meta["horizon"],
            dropout=args.dropout,
            stacked=args.stacked
        ).to(device)
        print(model)

        optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
        loss_fn = nn.MSELoss()

        best_val_loss = float('inf')
        patience_counter = 0

        run_out_dir = os.path.join(args.out_dir, args.run_name)
        os.makedirs(run_out_dir, exist_ok=True)

        for epoch in range(1, args.epochs + 1):
            train_loss, train_mae = train_one_epoch(model, train_loader, loss_fn, optimizer, device)
            val_loss, val_mae, _ = validate(model, val_loader, loss_fn, device)

            print(f"Epoch {epoch:03d}: "
                  f"Train Loss {train_loss:.4f}, Train MAE {train_mae:.4f} | "
                  f"Val Loss {val_loss:.4f}, Val MAE {val_mae:.4f}")

            mlflow.log_metric("train_loss", train_loss, step=epoch)
            mlflow.log_metric("train_mae", train_mae, step=epoch)
            mlflow.log_metric("val_loss", val_loss, step=epoch)
            mlflow.log_metric("val_mae", val_mae, step=epoch)

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                torch.save(model.state_dict(), os.path.join(run_out_dir, "best_model.pt"))
                print(f"✅ Saved best model at epoch {epoch}")
            else:
                patience_counter += 1
                if patience_counter >= args.patience:
                    print(f"⏹️  Early stopping at epoch {epoch}")
                    break

            if epoch % (args.patience // 2) == 0:
                for param_group in optimizer.param_groups:
                    param_group['lr'] *= 0.5
                print(f"🔽 Reduced LR to {optimizer.param_groups[0]['lr']}")

        _, _, y_pred = validate(model, val_loader, loss_fn, device)
        np.save(os.path.join(run_out_dir, "y_val.npy"), y_val)
        np.save(os.path.join(run_out_dir, "y_pred.npy"), y_pred)
        joblib.dump(scaler, os.path.join(run_out_dir, "scaler.pkl"))
        with open(os.path.join(run_out_dir, "meta.json"), "w") as f:
            json.dump(meta, f)

        mlflow.log_artifacts(run_out_dir)
        print("✅ Training complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train LSTM for Air Traffic Congestion Prediction")
    parser.add_argument("--windows_dir", default="data/processed/windows", help="Directory with .npz window files")
    parser.add_argument("--out_dir", default="artifacts", help="Base output directory")
    parser.add_argument("--mlflow_uri", default="file:./mlruns", help="MLflow Tracking URI")
    parser.add_argument("--experiment", default="air_traffic_congestion", help="MLflow experiment name")
    parser.add_argument("--run_name", default="lstm_run", help="MLflow run name")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--hidden_size", type=int, default=64)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--stacked", action="store_true", help="Use 2-layer stacked LSTM")
    args = parser.parse_args()
    main(args)
