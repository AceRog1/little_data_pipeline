import os
import numpy as np
import pandas as pd
import mlflow
import mlflow.tensorflow
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional, LayerNormalization
from sklearn.preprocessing import StandardScaler
import argparse

# ---------- helpers ----------
def make_windows(arr, lookback, horizon):
    """arr shape: (T, n_feat) -> X:(N,lookback,n_feat), y:(N,horizon)  (y = primera columna)"""
    X, y = [], []
    for i in range(len(arr) - lookback - horizon):
        X.append(arr[i:i + lookback])
        y.append(arr[i + lookback:i + lookback + horizon, 0])
    return np.array(X), np.array(y)


def save_scaler_stats(scaler, folder):
    txt_path = os.path.join(folder, "scaler_stats.txt")
    with open(txt_path, "w") as f:
        f.write(f"{scaler.mean_[0]},{scaler.scale_[0]}")
    return txt_path


# ---------- main ----------
def main(cfg):
    # 0) MLflow
    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment("congestion")

    with mlflow.start_run(run_name=cfg.run_name):
        mlflow.log_params(vars(cfg))

        # 1) leer archivo Parquet
        df = pd.read_parquet(cfg.input_parquet)
        df = df.reset_index()  # Asegúrate de que 'minute' sea una columna normal

        # 2) Convertir 'minute' (Timestamp) a segundos desde la época
        df["minute"] = df["minute"].astype(np.int64) // 10**9

        # 3) Escalar las columnas
        scaler = StandardScaler()
        df[["minute", "congestion"]] = scaler.fit_transform(df[["minute", "congestion"]])

        # 4) Preparar los datos
        data = df[["minute", "congestion"]].values.astype("float32")

        # 5) Dividir los datos secuenciales para series temporales
        split_idx = int(len(data) * (1 - cfg.test_size))
        X_train, X_val = data[:split_idx, :], data[split_idx:, :]

        # 6) Crear ventanas de datos
        X_train, y_train = make_windows(X_train, cfg.lookback, cfg.horizon)
        X_val, y_val = make_windows(X_val, cfg.lookback, cfg.horizon)

        # 7) Crear y entrenar el modelo
        model = Sequential([
            Bidirectional(LSTM(cfg.hidden_size, return_sequences=True, dropout=cfg.dropout, recurrent_dropout=cfg.dropout), input_shape=(cfg.lookback, 2)),
            LayerNormalization(),
            Bidirectional(LSTM(cfg.hidden_size // 2, dropout=cfg.dropout, recurrent_dropout=cfg.dropout)),
            LayerNormalization(),
            Dense(cfg.dense_units, activation="relu"),
            Dropout(cfg.dropout),
            Dense(cfg.horizon)
        ])
        model.compile(optimizer=tf.keras.optimizers.Adam(cfg.lr), loss="mse", metrics=["mae"])

        # 8) Callbacks
        callbacks = [
            tf.keras.callbacks.EarlyStopping(patience=cfg.patience, restore_best_weights=True, verbose=1),
            tf.keras.callbacks.ReduceLROnPlateau(patience=cfg.patience // 2, factor=0.5, verbose=1)
        ]

        # 9) Entrenamiento y registro de métricas por época
        history = model.fit(X_train, y_train, validation_data=(X_val, y_val),
                            epochs=cfg.epochs, batch_size=cfg.batch_size, callbacks=callbacks)

        for epoch in range(len(history.history['loss'])):
            mlflow.log_metric("loss", history.history['loss'][epoch], step=epoch)
            mlflow.log_metric("mae", history.history['mae'][epoch], step=epoch)

        # 10) Guardar el modelo y artefactos
        output_dir = os.path.join(cfg.out_dir, cfg.run_name)
        os.makedirs(output_dir, exist_ok=True)

        model.save(os.path.join(output_dir, "lstm_congestion.keras"))
        save_scaler_stats(scaler, output_dir)

        # --- 🔁 Guardar y registrar predicciones ---
        y_pred = model.predict(X_val)
        np.save(os.path.join(output_dir, "y_val.npy"), y_val)
        np.save(os.path.join(output_dir, "y_pred.npy"), y_pred)
        mlflow.log_artifact(os.path.join(output_dir, "y_val.npy"))
        mlflow.log_artifact(os.path.join(output_dir, "y_pred.npy"))

        mlflow.log_artifacts(output_dir)
        print(f"✅ Modelo y predicciones guardados en {output_dir}")


# ---------- CLI ----------
if __name__ == "__main__":
    P = argparse.ArgumentParser(description="Entrenamiento LSTM para predecir congestión aérea")
    P.add_argument("--input_parquet", default="data/processed/congestion_minute.parquet")
    P.add_argument("--lookback", type=int, default=6)
    P.add_argument("--horizon", type=int, default=3)
    P.add_argument("--hidden_size", type=int, default=32)
    P.add_argument("--dense_units", type=int, default=16)
    P.add_argument("--dropout", type=float, default=0.3)
    P.add_argument("--stacked", action="store_true")
    P.add_argument("--lr", type=float, default=1e-3)
    P.add_argument("--test_size", type=float, default=0.2)
    P.add_argument("--epochs", type=int, default=200)
    P.add_argument("--batch_size", type=int, default=32)
    P.add_argument("--patience", type=int, default=30)
    P.add_argument("--run_name", default="lstm_run")
    P.add_argument("--out_dir", default="artifacts")
    cfg = P.parse_args()
    main(cfg)
