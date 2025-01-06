import json
import pika
import logging
from confluent_kafka import Consumer
from config import KAFKA_CONFIG, RABBITMQ_HOST, RABBITMQ_QUEUE

# Set up logging
logger = logging.getLogger('kafka_consumer')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def consume_messages(kafka_config):
    """Consumes messages from Kafka topics and pushes them to RabbitMQ queue."""
    consume_topic_name = "emails-topic-new"
    kafka_config["group.id"] = "python-group-1"  # Consumer-specific property
    kafka_config["auto.offset.reset"] = "earliest"  # Consumer-specific property
    consumer = Consumer(kafka_config)
    consumer.subscribe([consume_topic_name])

    # RabbitMQ connection and channel setup
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

    logger.info("Kafka consumer listening for messages...")
    try:
        while True:
            msg = consumer.poll(1.0)  # Poll messages every second
            if msg is not None and not msg.error():
                logger.info(f"Consumed message: {msg.value().decode('utf-8')}")
                
                email_data = json.loads(msg.value().decode('utf-8'))

                # Push the consumed email data to RabbitMQ
                email_message = {
                    'subject': email_data.get('subject'),
                    'snippet': email_data.get('snippet'),
                    'body': email_data.get('body'),
                    'id': email_data.get('id')
                }

                # Log the email being sent to RabbitMQ
                logger.info(f"Sending email to RabbitMQ with ID: {email_message['id']}")

                channel.basic_publish(
                    exchange='',
                    routing_key=RABBITMQ_QUEUE,  # Queue name
                    body=json.dumps(email_message),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Make the message persistent
                    ))

                logger.info(f"Message sent to RabbitMQ: {email_message['id']}")

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        connection.close()


if __name__ == "__main__":
    consume_messages(KAFKA_CONFIG) 