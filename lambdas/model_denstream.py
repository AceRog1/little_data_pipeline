import boto3
import json
import base64
from datetime import datetime

# Cliente S3
s3 = boto3.client('s3')

# Token de seguridad
EXPECTED_TOKEN = "midemosecreto123"

def lambda_handler(event, context):
    """
    Función Lambda para guardar modelos DenStream en S3
    """
    
    try:
        # CORRECCIÓN: Verificar si el payload viene en 'body' (Function URL)
        if 'body' in event:
            # Si viene de Function URL, el payload está en body como string JSON
            if isinstance(event['body'], str):
                event_data = json.loads(event['body'])
            else:
                event_data = event['body']
        else:
            # Si viene de invocación directa
            event_data = event
        
        print(f"DEBUG: Event recibido: {json.dumps(event_data, indent=2)}")
        
        # Verificar token de seguridad
        token = event_data.get('token')
        print(f"DEBUG: Token recibido: '{token}'")
        print(f"DEBUG: Token esperado: '{EXPECTED_TOKEN}'")
        
        if token != EXPECTED_TOKEN:
            return {
                'statusCode': 401,
                'body': json.dumps({
                    'success': False,
                    'error': 'Token de seguridad inválido',
                    'debug': {
                        'token_received': token,
                        'token_expected': EXPECTED_TOKEN,
                        'token_match': token == EXPECTED_TOKEN
                    }
                })
            }
        
        # Verificar acción
        action = event_data.get('action')
        if action != 'upload_model':
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': f'Acción no soportada: {action}. Solo se soporta "upload_model"'
                })
            }
        
        # Obtener parámetros requeridos
        bucket = event_data.get('bucket')
        key = event_data.get('key')
        model_data = event_data.get('model_data')
        
        # Validar parámetros
        if not bucket:
            return create_error_response(400, 'Parámetro "bucket" es requerido')
        
        if not key:
            return create_error_response(400, 'Parámetro "key" es requerido')
        
        if not model_data:
            return create_error_response(400, 'Parámetro "model_data" es requerido')
        
        # Decodificar datos del modelo desde base64
        try:
            model_bytes = base64.b64decode(model_data)
            model_size = len(model_bytes)
        except Exception as e:
            return create_error_response(400, f'Error decodificando modelo: {str(e)}')
        
        # Verificar que el modelo no esté vacío
        if model_size == 0:
            return create_error_response(400, 'El modelo está vacío')
        
        # Subir modelo a S3
        try:
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=model_bytes,
                ContentType='application/octet-stream',
                Metadata={
                    'uploaded_at': datetime.utcnow().isoformat(),
                    'content_type': 'denstream_model',
                    'size_bytes': str(model_size),
                    'uploaded_by': 'denstream_training_script'
                }
            )
            
            # Respuesta exitosa
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'message': 'Modelo guardado exitosamente en S3',
                    'bucket': bucket,
                    'key': key,
                    'size_bytes': model_size,
                    'uploaded_at': datetime.utcnow().isoformat()
                })
            }
            
        except boto3.exceptions.botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'NoSuchBucket':
                return create_error_response(404, f'El bucket "{bucket}" no existe')
            elif error_code == 'AccessDenied':
                return create_error_response(403, 'Acceso denegado al bucket S3')
            else:
                return create_error_response(500, f'Error de S3: {error_message}')
                
        except Exception as e:
            return create_error_response(500, f'Error subiendo modelo a S3: {str(e)}')
    
    except Exception as e:
        return create_error_response(500, f'Error interno del servidor: {str(e)}')

def create_error_response(status_code, error_message):
    """Helper para crear respuestas de error consistentes"""
    return {
        'statusCode': status_code,
        'body': json.dumps({
            'success': False,
            'error': error_message
        })
    }