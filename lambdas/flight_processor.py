import json
import boto3
import os
from datetime import datetime, timezone

s3 = boto3.client('s3')
BUCKET = 's3-project-little-data'

SECRET_TOKEN = os.getenv('SECRET_TOKEN', 'midemosecreto123')

def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method")
    if method != "POST":
        return {"statusCode": 405, "body": "Método no permitido"}

    try:
        body = json.loads(event.get("body", "{}"))
    except Exception as e:
        return {"statusCode": 400, "body": f"JSON inválido: {str(e)}"}

    if body.get("token") != SECRET_TOKEN:
        return {"statusCode": 403, "body": "Token inválido"}

    ts = datetime.now(timezone.utc).strftime('%Y/%m/%d/%H/%M%S%f')
    key = f"raw/new_flight/{ts}.json"
    
    body.pop("token", None)

    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=json.dumps(body)
    )

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Datos guardados en S3', 'key': key})
    }