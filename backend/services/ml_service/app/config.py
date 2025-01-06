# config.py

# Kafka Cloud Configuration
KAFKA_CONFIG = {
    "bootstrap.servers": "pkc-619z3.us-east1.gcp.confluent.cloud:9092",  # Cloud-hosted Kafka broker
    "security.protocol": "SASL_SSL",
    "sasl.mechanisms": "PLAIN",
    "sasl.username": "CFAIVUXPP46AIDVS",  # Cloud Kafka API Key
    "sasl.password": "s9bSJiQZ961Bmtvhl7is+lrvlpmmDL4LRykchMqwkVHbEFIAoX3X8jMiHAcY4TTA",  # Cloud Kafka Secret
    # Best practice for higher availability in librdkafka clients prior to 1.7
    "session.timeout.ms": "45000",
    "client.id":"ccloud-python-client-b10b42c7-94be-41b7-b2ab-1af8ca602cdd"
}

# RabbitMQ Configuration
RABBITMQ_HOST = 'localhost'  # Change if necessary
RABBITMQ_QUEUE = 'email_queue'
REDIS_HOST = 'localhost'

# Model Configuration
MODEL_NAME = "ealvaradob/bert-finetuned-phishing"

