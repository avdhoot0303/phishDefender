import threading
import time
import pika
import redis
import json
import logging
from confluent_kafka import Consumer, Producer
from wsgiref.simple_server import make_server
from config import KAFKA_CONFIG, RABBITMQ_HOST, RABBITMQ_QUEUE, MODEL_NAME, REDIS_HOST
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

# Set up logging
logger = logging.getLogger('app')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Initialize Redis
redis_client = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

# Initialize Model
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

# Create the Falcon app for API
import falcon

class EmailPredictionResource:
    def on_get(self, req, resp):
        """Get email prediction results from Redis"""
        email_id = req.get_param('email_id')
        if not email_id:
            resp.media = {"error": "email_id is required"}
            resp.status = falcon.HTTP_400
            return
        
        # Fetch prediction result from Redis
        cached_result = redis_client.get(f"prediction:{email_id}")
        
        if not cached_result:
            resp.media = {"error": "Prediction result not found for this email ID"}
            resp.status = falcon.HTTP_404
            return
        
        resp.media = json.loads(cached_result)
        resp.status = falcon.HTTP_200

# Create Falcon application and add routes
app = falcon.App()
email_prediction_resource = EmailPredictionResource()
app.add_route('/api/get_email_prediction', email_prediction_resource)

# Kafka Consumer: Consume messages from Kafka
def consume_messages():
    kafka_config = KAFKA_CONFIG
    consume_topic_name = "emails-topic-new"
    kafka_config["group.id"] = "python-group-1"
    kafka_config["auto.offset.reset"] = "earliest"
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
                channel.basic_publish(
                    exchange='',
                    routing_key=RABBITMQ_QUEUE,  # Queue name
                    body=json.dumps(email_data),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Make the message persistent
                    )
                )
                logger.info(f"Message sent to RabbitMQ: {email_data['id']}")
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        connection.close()

# Prediction Service: Consume messages from RabbitMQ, run predictions
def process_email_prediction(ch, method, properties, body):
    """Process an email from RabbitMQ and push results to Kafka."""
    try:
        email = json.loads(body.decode())
        logger.info(f"Processing email with ID: {email['id']}")

        # Run the model inference
        email_text = f"Subject: {email['subject']} - {email['snippet']} - {email['body']}"
        inputs = tokenizer(email_text, return_tensors="pt", truncation=True, padding=True)
        outputs = model(**inputs)
        probabilities = F.softmax(outputs.logits, dim=-1).detach().numpy()[0].tolist()
        predicted_class = outputs.logits.argmax(dim=-1).item()

        result = {
            "id": email['id'],
            "predicted_label": "Phishing" if predicted_class == 1 else "Not Phishing",
            "probabilities": {"Not Phishing": probabilities[0], "Phishing": probabilities[1]},
            "reason": "The email contains patterns commonly associated with phishing attempts."
        }

        # Cache the result in Redis
        redis_client.set(f"prediction:{email['id']}", json.dumps(result), ex=3600)  # TTL of 1 hour
        logger.info(f"Prediction result for email ID {email['id']} cached in Redis.")

        # Produce result to Kafka
        kafka_producer = Producer(KAFKA_CONFIG)
        kafka_producer.produce("detection_results_single", key=email['id'], value=json.dumps(result))
        kafka_producer.flush()
        logger.info(f"Prediction result for email ID {email['id']} sent to Kafka.")

        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error processing email: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

def start_prediction_service():
    """Start consuming messages from RabbitMQ."""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=process_email_prediction)

        logger.info("RabbitMQ prediction service started. Waiting for messages...")
        channel.start_consuming()
    except Exception as e:
        logger.error(f"Error starting RabbitMQ consumer: {e}")

# Main function to start all services
def main():
    # Start Kafka consumer in a separate thread
    consumer_thread = threading.Thread(target=consume_messages, daemon=True)
    consumer_thread.start()

    # Start the prediction service in a separate thread
    prediction_thread = threading.Thread(target=start_prediction_service, daemon=True)
    prediction_thread.start()

    # Start the Falcon API
    logger.info("Starting Falcon API server...")
    httpd = make_server('127.0.0.1', 8000, app)  # Start Falcon API
    httpd.serve_forever()

if __name__ == "__main__":
    main()
