import json
import pika
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F
from confluent_kafka import Producer
from config import KAFKA_CONFIG, RABBITMQ_HOST, RABBITMQ_QUEUE, MODEL_NAME
import logging
import re 
# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

# Kafka Producer to send results back
def get_kafka_producer():
    return Producer(KAFKA_CONFIG)

# Function to clean text
def clean_text(text):
    text = text.replace("\r\n", " ")
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    text = text.encode('ascii', 'ignore').decode()
    return text

# Function to process email prediction from RabbitMQ and send results to Kafka
def process_email_prediction(ch, method, properties, body):
    """Process an email prediction from RabbitMQ and push results to Kafka."""
    email = json.loads(body.decode())

    # Prepare the email text for prediction
    email_text = f"Subject: {email['subject']} - {email['snippet']} - {email['body']}"

    # Tokenize and predict
    inputs = tokenizer(email_text, return_tensors="pt", truncation=True, padding=True)
    outputs = model(**inputs)
    probabilities = F.softmax(outputs.logits, dim=-1).detach().numpy()[0].tolist()
    predicted_class = outputs.logits.argmax(dim=-1).item()

    # Generate the result
    result = {
        "id": email['id'],
        "predicted_label": "Phishing" if predicted_class == 1 else "Not Phishing",
        "probabilities": {"Not Phishing": probabilities[0], "Phishing": probabilities[1]},
        "reason": "The email contains patterns commonly associated with phishing attempts."
    }

    # Log the result
    logger.info(f"Processed email id: {email['id']} - Prediction: {result['predicted_label']}")

    # Send prediction results back to Kafka
    kafka_producer = get_kafka_producer()
    kafka_producer.produce("prediction_results", key=email['id'], value=json.dumps(result))
    kafka_producer.flush()

    # Acknowledge the message
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Start the RabbitMQ consumer in a separate thread
def start_prediction_service():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()

    # Declare the queue to ensure it exists
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

    # Set up the consumer
    channel.basic_qos(prefetch_count=1)  # Process one message at a time
    channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=process_email_prediction)

    logger.info("Prediction service started. Waiting for emails...")
    channel.start_consuming()
