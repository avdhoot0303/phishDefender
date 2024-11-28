from kafka import KafkaConsumer
import json

# Kafka consumer setup
consumer = KafkaConsumer(
    'emails-topic',
    bootstrap_servers=['ams560_project-kafka-broker-1-1:9092'],
    group_id='email-consumer-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# Listen for messages and print them
for message in consumer:
    print(f"Received email: {message.value}")
    # You can process the message further, like storing it in a database
