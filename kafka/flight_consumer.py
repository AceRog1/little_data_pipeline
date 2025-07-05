from confluent_kafka import Consumer, KafkaException, KafkaError
import json
import requests

# La URL que copiaste
LAMBDA_URL = "https://s6fvvden5q7abf6zozyej6u4hi0jyhvg.lambda-url.us-east-1.on.aws/"

def invoke_lambda_via_http(data):
    data["token"] = "midemosecreto123"

    resp = requests.post(LAMBDA_URL, json=data, timeout=5)
    if resp.status_code != 200:
        print(f"Error llamando Lambda: {resp.status_code}, {resp.text}")
    else:
        print("Payload enviado por HTTP a Lambda OK")

def run():
    conf = {
        'bootstrap.servers': '52.205.209.139',
        'group.id': 'datalake',
        'auto.offset.reset': 'earliest'
    }
    consumer = Consumer(conf)
    consumer.subscribe(['flight_stream'])
    print("Consumer local activo, escuchando...")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())

            data = json.loads(msg.value().decode('utf-8'))
            invoke_lambda_via_http(data)

    except KeyboardInterrupt:
        print("Interrupción por usuario, cerrando consumer...")
    finally:
        consumer.close()

if __name__ == "__main__":
    run()
