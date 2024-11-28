from kafka import KafkaProducer
import json
import logging

# Kafka settings
KAFKA_BROKER = 'kafka-broker-1:9092'  # Kafka broker address
TOPIC_NAME = 'new-emails'  # Kafka topic name

# Setup Kafka producer
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')  # Serialize messages to JSON
)

def send_to_kafka(message):
    """Send message to Kafka topic."""
    try:
        producer.send(TOPIC_NAME, value=message)
        logging.info(f"Message sent to Kafka: {message}")
    except Exception as e:
        logging.error(f"Failed to send message to Kafka: {e}")
