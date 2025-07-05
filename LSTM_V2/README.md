# Air Traffic Congestion LSTM Forecasting

Este proyecto usa un modelo LSTM (PyTorch) para predecir la congestión aérea (conteo de aeronaves) en celdas espacio-temporales. Incluye todo el flujo: limpieza, ventanas, entrenamiento con grid search y MLflow, evaluación, predicciones nuevas y rolling forecast.

---

## 📦 Estructura de carpetas

```
.
├── data/
│   ├── raw/                     ← Datos CSV o Parquet originales
│   └── processed/               ← Datos procesados, scaler.pkl, ventanas
├── artifacts/                   ← Modelos entrenados y outputs auxiliares
├── mlruns/                      ← Experimentos de MLflow
├── outputs/                     ← Gráficos y predicciones
└── src/
    ├── data/
    │   ├── prepare_dataset.py
    │   ├── create_windows.py
    │   └── make_seed_window.py
    ├── models/
    │   ├── train_lstm.py
    │   ├── grid_search_lstm.py
    │   ├── evaluate_best_model.py
    │   └── rolling_forecast.py
    └── visualization/
        ├── plot_predictions.py
        ├── plot_roll_forecast.py
        ├── predict_new_window.py
        └── show_prediction_table.py
```

---

## 🚀 Flujo de ejecución paso a paso

### 1️⃣ Preparar dataset crudo

```bash
python src/data/prepare_dataset.py --input_dir data/raw --out_dir data/processed
```

✔️ Limpia y agrupa datos crudos. ✔️ Genera `aggregated_congestion.parquet` y `scaler.pkl`.

### 2️⃣ Crear ventanas de entrenamiento

```bash
python src/data/create_windows.py --input_file data/processed/aggregated_congestion.parquet --out_dir data/processed/windows
```

✔️ Usa lookback/horizon. ✔️ Genera: `X_train.npz`, `y_train.npz`, `X_val.npz`, `y_val.npz`, `meta.json`.

### 3️⃣ Hacer grid search con MLflow

```bash
python src/models/grid_search_lstm.py
```

✔️ Lanza combinaciones de hyperparámetros. ✔️ Registra runs en `mlruns/`.

### 4️⃣ Revisar resultados en MLflow UI

```bash
mlflow ui
```

✔️ Abrir [http://localhost:5000](http://localhost:5000). ✔️ Filtrar por `val_loss` o `val_mae` para elegir el mejor modelo.

### 5️⃣ Evaluar el mejor modelo

```bash
python src/models/evaluate_best_model.py \
  --model_path "mlruns/<experiment_id>/<run_id>/artifacts/best_model.pt" \
  --windows_dir data/processed/windows \
  --out_dir outputs \
  --hidden_size <valor> \
  --dropout <valor> \
  [--stacked]
```

✔️ Guarda gráficos prediction\_vs\_real\_t+1.png, etc. ✔️ CSV con predicciones.

### 6️⃣ Hacer rolling forecast para predecir a futuro

**(a) Crear ventana semilla**

```bash
python src/data/make_seed_window.py --windows_dir data/processed/windows --out_file my_start_window.npy
```

✔️ Toma última ventana validada como seed.

**(b) Ejecutar rolling forecast**

```bash
python src/models/rolling_forecast.py \
  --model_path "mlruns/<experiment_id>/<run_id>/artifacts/best_model.pt" \
  --meta_file data/processed/windows/meta.json \
  --start_window my_start_window.npy \
  --scaler_file data/processed/scaler.pkl \
  --out_dir outputs \
  --steps_ahead 12 \
  --hidden_size <valor> \
  --dropout <valor> \
  [--stacked]
```

✔️ Genera `rolling_predictions.npy` en outputs.

**(c) Graficar forecast y picos**

```bash
python src/visualization/plot_roll_forecast.py --pred_file outputs/rolling_predictions.npy --out_file outputs/forecast_plot.png --threshold 1
```

✔️ Visualiza la serie futura. ✔️ Destaca puntos sobre umbral como "picos de congestión".

---

## ✅ Requerimientos

```
pandas
numpy
torch
mlflow
pyarrow
scikit-learn
matplotlib
tqdm
```

Instalar:

```bash
pip install -r requirements.txt
```

---

## 🎯 Objetivo

Predecir la evolución futura del conteo de aeronaves (congestión y descongestión) en cada celda espacio-temporal para asistir a planificadores y controladores aéreos.

