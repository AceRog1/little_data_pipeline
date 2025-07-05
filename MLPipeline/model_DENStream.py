import numpy as np
from river.cluster import DenStream
import mlflow
import pickle
import os
import logging
import requests
import base64
import pandas as pd
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
import time
from datetime import datetime

# ─────────────── Config MLflow ───────────────
mlflow.set_tracking_uri("http://127.0.0.1:8082")
experiment_name = "DenStream_Experiment"
mlflow.set_experiment(experiment_name)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────── Config Lambda ───────────────
LAMBDA_URL = "https://xoahs3zzh2ry4q3lvbgupnnr2m0octoa.lambda-url.us-east-1.on.aws/"
TOKEN = "midemosecreto123"

def invoke_lambda_upload(model_file_path, bucket, key):
    with open(model_file_path, "rb") as f:
        model_bytes = f.read()

    model_base64 = base64.b64encode(model_bytes).decode("utf-8")

    payload = {
        "token": TOKEN,
        "action": "upload_model",
        "bucket": bucket,
        "key": key,
        "model_data": model_base64
    }

    try:
        response = requests.post(LAMBDA_URL, json=payload)
        logger.info(f"Lambda response: {response.status_code} - {response.text}")
        return response.json()
    except Exception as e:
        logger.error(f"Error invocando Lambda: {str(e)}")
        return {}

def get_next_version_number():
    """Obtiene el siguiente número de versión basado en runs anteriores."""
    client = mlflow.tracking.MlflowClient()
    experiment = client.get_experiment_by_name(experiment_name)
    runs = client.search_runs([experiment.experiment_id])

    count = 0
    for run in runs:
        run_name = run.data.tags.get("mlflow.runName", "")
        if run_name.startswith("denstream_v"):
            count += 1
    return count + 1

# ─────────────── Entrenamiento ───────────────
def train_denstream_model(df, config):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[['x_km', 'y_km']])

    clusterer = DenStream(
        epsilon=config['epsilon'],
        beta=config['beta'],
        mu=config['mu'],
        decaying_factor=config['decaying_factor']
    )

    start_time = time.time()

    for row in X_scaled:
        clusterer.learn_one({0: row[0], 1: row[1]})

    end_time = time.time()
    train_duration_sec = end_time - start_time
    n_samples = len(X_scaled)
    avg_samples_per_sec = n_samples / train_duration_sec if train_duration_sec > 0 else 0

    mlflow.log_metric("train_duration_sec", train_duration_sec)
    mlflow.log_metric("n_samples", n_samples)
    mlflow.log_metric("avg_samples_per_sec", avg_samples_per_sec)

    centers = [
        np.array(list(mc.calc_center(clusterer.timestamp).values()))
        for mc in clusterer.p_micro_clusters.values()
    ]

    if len(centers) > 1:
        labels = [
            int(np.argmin([np.linalg.norm(pt - c) for c in centers]))
            for pt in X_scaled
        ]
        if len(set(labels)) > 1:
            silhouette = silhouette_score(X_scaled, labels)
            logger.info(f"Silhouette score: {silhouette:.4f}")
            mlflow.log_metric("silhouette_score", silhouette)
        else:
            logger.info("No hay variedad de etiquetas para Silhouette")
            mlflow.log_metric("silhouette_score", -1)
    else:
        logger.info("Menos de 2 micro-clusters; no se calcula Silhouette")
        mlflow.log_metric("silhouette_score", -1)

    return clusterer, scaler

# ─────────────── Pipeline principal ───────────────
def model_DENStream():
    logger.info("Cargando dataset...")
    df = pd.read_csv("/home/ubuntu/datasets/temp/preprocessing_part_2.csv")

    config = {
        'epsilon': 1.0,
        'beta': 0.2,
        'mu': 20,
        'decaying_factor': 0.0001
    }

    version_number = get_next_version_number()
    today_str = datetime.now().strftime("%Y-%m-%d")
    run_name = f"denstream_v{version_number}_{today_str}"

    mlflow.start_run(run_name=run_name)

    logger.info(f"Iniciando entrenamiento con config: {config}")
    mlflow.log_params(config)

    clusterer, scaler = train_denstream_model(df, config)

    os.makedirs("/home/ubuntu/model/temp", exist_ok=True)
    scaler_path = "/home/ubuntu/model/temp/scaler.pkl"
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    mlflow.log_artifact(scaler_path)

    model_path = "/home/ubuntu/model/temp/DENStream.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(clusterer, f)
    mlflow.log_artifact(model_path)

    bucket_name = "s3-project-little-data"
    s3_key = f"denstream/{run_name}.pkl"   # Nombre en S3 con versión y fecha
    response = invoke_lambda_upload(model_path, bucket_name, s3_key)

    logger.info(f"Respuesta Lambda: {response}")

    logger.info("Entrenamiento y log de métricas finalizado.")
    mlflow.end_run()

if __name__ == "__main__":
    model_DENStream()
