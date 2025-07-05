import boto3
import json
import csv
import os

def csv_compiler():
    LAMBDA_NAME = 'daily_extractor'
    REGION_NAME = 'us-east-1'

    lambda_client = boto3.client('lambda', region_name=REGION_NAME)
    s3_client = boto3.client('s3', region_name=REGION_NAME)

    # Invocamos Lambda
    print("Invocando Lambda para obtener bucket y key...")
    resp = lambda_client.invoke(
        FunctionName=LAMBDA_NAME,
        InvocationType='RequestResponse',
        Payload=json.dumps({})
    )
    payload = json.load(resp['Payload'])
    if payload.get("statusCode") != 200:
        print(f"❌ Error en Lambda: {payload.get('body')}")
        return
    body = json.loads(payload['body'])
    bucket = body['bucket']
    key = body['key']

    print(f"Bucket: {bucket}")
    print(f"Key: {key}")

    # Descargar JSON localmente
    tmp_json_path = '/tmp/daily.json'
    print("Descargando JSON desde S3...")
    s3_client.download_file(bucket, key, tmp_json_path)
    print(f"JSON descargado en: {tmp_json_path}")

    # Leer JSON
    with open(tmp_json_path, 'r') as f:
        data = json.load(f)

    if not data:
        print("JSON vacío, no se generará CSV.")
        return

    # Preparar carpeta
    tmp_dir = os.path.expanduser('~/datasets/temp')
    os.makedirs(tmp_dir, exist_ok=True)

    csv_path_tmp = os.path.join(tmp_dir, 'all_data.csv')

    # Convertir a CSV en tmp_dir
    print("Convirtiendo a CSV...")
    with open(csv_path_tmp, 'w', newline='') as f:
        fieldnames = list(data[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in data:
            writer.writerow(record)

    print(f"✅ CSV generado en: {csv_path_tmp}")

if __name__ == "__main__":
    csv_compiler()
