import json
import boto3
import os
from datetime import datetime, timedelta, timezone

# Cliente de S3
s3 = boto3.client('s3')

# Configuración
BUCKET = 's3-project-little-data'

def lambda_handler(event, context):
    start_time = datetime.now()
    print(f"[{start_time.isoformat()}] Lambda daily_flight_1 iniciada por invocación directa")

    try:
        now = datetime.now(timezone.utc)

        # Leer el modo desde el evento (hoy o ayer)
        mode = "ayer"
        if isinstance(event, dict) and "mode" in event:
            mode = event["mode"]

        # Determinar la fecha
        dia = now if mode == "hoy" else now - timedelta(days=1)

        year = dia.strftime("%Y")
        month = dia.strftime("%m")
        day = dia.strftime("%d")

        prefix_base = f"concatenated/{year}/{month}/{day}/"
        print(f"🧪 MODE: {mode}")
        print(f"📅 DIA: {dia.strftime('%Y-%m-%d')}")
        print(f"📁 PREFIX BASE: {prefix_base}")

        all_entries = []

        # Listar todos los archivos en la carpeta del día
        response = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix_base)
        if "Contents" in response:
            for obj in response["Contents"]:
                key = obj["Key"]
                if key.endswith(".json"):
                    print(f"🔍 Leyendo archivo: {key}")
                    try:
                        obj_data = s3.get_object(Bucket=BUCKET, Key=key)
                        contenido = obj_data['Body'].read().decode('utf-8')
                        datos = json.loads(contenido)
                        all_entries.extend(datos)
                    except Exception as e:
                        print(f"⚠️ Error leyendo {key}: {e}")
        else:
            print("🚫 No se encontraron archivos JSON para esta fecha.")

        print(f"✅ Archivos encontrados: {len(all_entries)}")
        print(f"🧩 Total de entradas concatenadas: {len(all_entries)}")

        # Guardar el resultado concatenado en daily_joined/
        new_key = f"daily_joined/{year}/{month}/{day}/daily.json"
        s3.put_object(
            Bucket=BUCKET,
            Key=new_key,
            Body=json.dumps(all_entries, indent=2).encode('utf-8'),
            ContentType='application/json'
        )
        print(f"📦 Archivo guardado exitosamente en: {new_key}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"{len(all_entries)} entradas guardadas en {new_key}",
            })
        }

    except Exception as e:
        print(f"💥 Error en Lambda: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }