
# Predicción de Congestión Aérea con LSTM

Este proyecto utiliza un modelo **LSTM (Long Short-Term Memory)** para predecir la congestión aérea basada en el tiempo de vuelo y las aeronaves. El modelo es entrenado con datos históricos de vuelos almacenados en un archivo Parquet. El proyecto está diseñado para probar diferentes configuraciones del modelo y comparar su rendimiento utilizando **MLflow**.

## Estructura del Proyecto

```
air_traffic_lstm/
├── artifacts/                        # Carpeta donde se almacenan los modelos y artefactos de entrenamiento
├── data/                             # Carpeta donde se almacenan los datos
│   ├── processed/                    # Datos procesados en formato Parquet
│   └── raw/                          # Archivos de datos crudos (CSV u otros)
├── src/
│   ├── data/                         # Scripts para procesamiento de datos
│   ├── models/                       # Scripts de entrenamiento de modelos
│   └── visualization/                 # Scripts para visualización de resultados
├── requirements.txt                  # Dependencias necesarias para ejecutar el proyecto
├── .gitignore                        # Archivos y carpetas a ser ignorados por git
└── README.md                         # Documentación del proyecto
```

## Requisitos

- **Python 3.7+**
- **MLflow**: para gestionar y registrar experimentos.
- **TensorFlow**: para entrenar el modelo LSTM.
- **Pandas**: para manipulación de datos.
- **NumPy**: para operaciones matemáticas y procesamiento de datos.
- **Scikit-learn**: para el escalado de datos.

### Instalación

Para instalar las dependencias del proyecto, puedes usar el siguiente comando:

```bash
pip install -r requirements.txt
```

### Uso del Proyecto

#### 1. **Preprocesamiento de Datos**

El primer paso es procesar los datos crudos y guardarlos en formato **Parquet** para facilitar el entrenamiento. Para ello, ejecuta el siguiente script:

```bash
python src/data/make_dataset.py
```

Este script leerá los archivos de datos crudos (`CSV`), los limpiará, los procesará y los almacenará en **Parquet** en la carpeta `data/processed/`.

#### 2. **Entrenamiento de Modelos**

Puedes entrenar el modelo LSTM con diferentes configuraciones utilizando el siguiente comando. Asegúrate de modificar los parámetros de acuerdo con las pruebas que deseas realizar.

```bash
python src/models/train_lstm.py --input_parquet data/processed/congestion_minute.parquet --epochs 200 --run_name <nombre_del_run> --lookback 6 --horizon 3
```

Este comando entrenará el modelo LSTM para predecir la congestión aérea. Los resultados del entrenamiento, incluyendo el modelo y las métricas de evaluación (como `loss` y `mae`), se registrarán en **MLflow**.

#### 3. **Automatización de Experimentos**

También puedes automatizar múltiples ejecuciones de experimentos con diferentes configuraciones utilizando un script `.bat`. Aquí tienes un ejemplo de cómo ejecutar varias configuraciones de entrenamiento con diferentes parámetros.

Ejecuta el archivo `.bat` para ejecutar diferentes experimentos:

```bash
run_all.bat
```

Este script ejecuta cinco experimentos con diferentes configuraciones de entrenamiento como:

- Variación de la tasa de aprendizaje.
- Diferentes valores de `lookback`.
- Diferentes tasas de `dropout`.

#### 4. **Visualización de Resultados**

Después de entrenar los modelos, puedes comparar las predicciones de los modelos con los valores reales. Ejecuta el siguiente script para generar un gráfico comparando las predicciones de todas las ejecuciones:

```bash
python src/visualization/plot_comparisons.py
```

Esto generará un gráfico guardado en `src/visualization/output/comparacion_runs.png`, donde se muestran las comparaciones entre las predicciones y los valores reales para cada ejecución.

#### 5. **MLflow para Gestionar Experimentos**

Puedes usar **MLflow** para gestionar y visualizar los resultados de los experimentos. Para iniciar la interfaz web de MLflow, ejecuta:

```bash
mlflow ui
```

Esto abrirá la interfaz web de **MLflow** en `http://127.0.0.1:5000`, donde podrás comparar los modelos, revisar las métricas (`loss`, `mae`), y ver los artefactos de cada corrida.

## Explicación del Código

- **`make_dataset.py`**: Lee los datos crudos, realiza las transformaciones necesarias, y guarda los datos procesados en formato **Parquet**.
- **`train_lstm.py`**: Carga los datos procesados, entrena el modelo LSTM para predecir la congestión aérea y registra los experimentos en **MLflow**.
- **`plot_comparisons.py`**: Compara las predicciones de los modelos entrenados visualizando las métricas `loss` y `mae`.

## Licencia

Este proyecto está bajo la **Licencia MIT**.