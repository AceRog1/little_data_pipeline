import boto3
import json

s3 = boto3.client('s3')

def lambda_handler(event, context):
    bucket = event.get('bucket', 's3-project-little-data')
    base_prefix = 'daily_joined/'

    years_resp = s3.list_objects_v2(Bucket=bucket, Prefix=base_prefix, Delimiter='/').get('CommonPrefixes', [])
    if not years_resp:
        return {'statusCode': 404, 'body': json.dumps({'error': 'No se encontraron años'})}
    years = sorted([p['Prefix'].split('/')[1] for p in years_resp], reverse=True)

    for year in years:
        months_resp = s3.list_objects_v2(Bucket=bucket, Prefix=f"{base_prefix}{year}/", Delimiter='/').get('CommonPrefixes', [])
        if not months_resp:
            continue
        months = sorted([p['Prefix'].split('/')[2] for p in months_resp], reverse=True)

        for month in months:
            days_resp = s3.list_objects_v2(Bucket=bucket, Prefix=f"{base_prefix}{year}/{month}/", Delimiter='/').get('CommonPrefixes', [])
            if not days_resp:
                continue
            days = sorted([p['Prefix'].split('/')[3] for p in days_resp], reverse=True)

            for day in days:
                key = f"{base_prefix}{year}/{month}/{day}/daily.json"
                try:
                    obj = s3.get_object(Bucket=bucket, Key=key)
                    content = obj['Body'].read().decode('utf-8')
                    json_data = json.loads(content)

                    if (isinstance(json_data, list) and len(json_data) > 0) or (isinstance(json_data, dict) and len(json_data.keys()) > 0):
                        print(f"✅ Archivo válido encontrado: {key}")
                        # ⚡ Devolver solo bucket y key
                        return {
                            'statusCode': 200,
                            'body': json.dumps({
                                'bucket': bucket,
                                'key': key
                            })
                        }
                    else:
                        print(f"⚠️ Archivo vacío: {key}")

                except Exception as e:
                    print(f"❌ Error leyendo {key}: {e}")

    return {'statusCode': 404, 'body': json.dumps({'error': 'No se encontró daily.json con data'})}