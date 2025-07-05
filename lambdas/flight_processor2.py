import json
import boto3
from datetime import datetime, timedelta, timezone
from botocore.exceptions import ClientError  # ✅ Necesario para detectar errores de S3

# Cliente de S3
s3 = boto3.client('s3')

# Configuración
BUCKET = 's3-project-little-data'

def lambda_handler(event, context):
    """
    Función Lambda invocada por EventBridge cada hora.
    Concatenará todos los JSONs subidos en las carpetas:
      - raw/new_flight/<YYYY/MM/DD/HH>/
      - raw/new_flight/<YYYY/MM/DD/(HH+1)>/
    Y los guardará en concatenated/<YYYY/MM/DD/HH>.json
    """
    now = datetime.now(timezone.utc)
    hora_anterior = now - timedelta(hours=1)

    start_iso = now.isoformat()
    print(f"[{start_iso}] Lambda iniciada por EventBridge")

    # Verificar conexión a S3
    try:
        s3.list_objects_v2(Bucket=BUCKET, MaxKeys=1)
        print(f"[{now.isoformat()}] Conexión a S3 exitosa ✅")
    except Exception as err:
        msg = str(err)
        print(f"[{now.isoformat()}] ❌ Error conectando a S3: {msg}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "No se pudo conectar al bucket S3", "detalle": msg})
        }

    # Prefijos de búsqueda y archivo de salida
    prefixes = [
        hora_anterior.strftime('raw/new_flight/%Y/%m/%d/%H/'),
        now.strftime('raw/new_flight/%Y/%m/%d/%H/')  # extra tolerancia
    ]
    output_key = hora_anterior.strftime('concatenated/%Y/%m/%d/%H.json')

    print(f"[{now.isoformat()}] Prefijos S3: {prefixes}")
    print(f"[{now.isoformat()}] Archivo destino: {output_key}")

    # Listar y concatenar objetos
    all_objects = []
    for prefix in prefixes:
        continuation_token = None
        while True:
            params = {'Bucket': BUCKET, 'Prefix': prefix}
            if continuation_token:
                params['ContinuationToken'] = continuation_token
            resp = s3.list_objects_v2(**params)
            contents = resp.get('Contents', [])
            all_objects.extend(contents)
            if not resp.get('IsTruncated'):
                break
            continuation_token = resp.get('NextContinuationToken')

    count = len(all_objects)
    print(f"[{datetime.now(timezone.utc).isoformat()}] Archivos encontrados: {count}")

    if count == 0:
        return {
            "statusCode": 404,
            "body": json.dumps({"message": "No se encontraron archivos para procesar", "prefixes": prefixes})
        }

    # Concatenar el contenido
    concatenated_data = []
    for idx, obj in enumerate(all_objects, start=1):
        key = obj['Key']
        print(f"[{datetime.now(timezone.utc).isoformat()}] Leyendo archivo {idx}/{count}: {key}")
        try:
            s3_obj = s3.get_object(Bucket=BUCKET, Key=key)
            text = s3_obj['Body'].read().decode('utf-8')
            data = json.loads(text)
            concatenated_data.append(data)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                print(f"[{datetime.now(timezone.utc).isoformat()}] ⚠️ Archivo no encontrado (omitido): {key}")
            else:
                print(f"[{datetime.now(timezone.utc).isoformat()}] ❌ Error al obtener {key}: {str(e)}")
            continue
        except json.JSONDecodeError:
            print(f"[{datetime.now(timezone.utc).isoformat()}] ❌ JSON inválido en {key}, omitiendo.")
            continue
        except Exception as e:
            print(f"[{datetime.now(timezone.utc).isoformat()}] ❌ Error al procesar {key}: {str(e)}")
            continue

    # Subir resultado final
    s3.put_object(
        Bucket=BUCKET,
        Key=output_key,
        Body=json.dumps(concatenated_data, ensure_ascii=False, indent=2),
        ContentType='application/json'
    )

    end_iso = datetime.now(timezone.utc).isoformat()
    print(f"[{end_iso}] Lambda finalizada. {len(concatenated_data)} objetos concatenados.")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Archivos concatenados correctamente",
            "output_key": output_key,
            "cantidad_archivos": len(concatenated_data)
        })
    }