# Kafka consumer logic
from kafka import KafkaConsumer
import json
from events.kafka_config import KAFKA_BROKER_URL, KAFKA_TOPIC_EMAILS

consumer = KafkaConsumer(
    KAFKA_TOPIC_EMAILS,
    bootstrap_servers=KAFKA_BROKER_URL,
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    value_deserializer=lambda v: json.loads(v.decode('utf-8'))
)

for message in consumer:
    print(f"Received message: {message.value}")
