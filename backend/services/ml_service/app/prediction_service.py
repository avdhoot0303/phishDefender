import json
import pika
import hashlib
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F
from confluent_kafka import Producer
import logging
import redis
from config import KAFKA_CONFIG, RABBITMQ_HOST, RABBITMQ_QUEUE, MODEL_NAME, REDIS_HOST
import re 
# Set up logging
logger = logging.getLogger('model_inference_service')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Initialize Redis
redis_client = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

# Initialize the model and tokenizer for inference
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

def get_kafka_producer():
    return Producer(KAFKA_CONFIG)

def generate_cache_key(email_data):
    """Generate a cache key based on the email content or sender."""
    # You can use sender or content, or both, depending on your caching strategy.
    sender = email_data.get('from', '')
    subject = email_data.get('subject', '')
    email_body = email_data.get('body', '')

    # Cache key could be a combination of sender and content
    content = f"{sender}:{subject}:{email_body}"
    
    # Generate a unique hash for the content
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def is_suspicious_sender(sender):
    """Check if the sender's email is from a suspicious domain."""
    suspicious_domains = ["example.com", "phishingsite.com"]  # Add known phishing domains
    sender_domain = sender.split('@')[-1]
    if sender_domain in suspicious_domains:
        return True
    return False

def contains_suspicious_content(email_text):
    """Check if the email body contains suspicious patterns."""
    suspicious_patterns = [
        r"\bfree\b",  # "free" is a common phishing keyword
        r"\burgent\b",  # Urgency is common in phishing emails
        r"\bclaim your prize\b",  # Often used in phishing
        r"[^a-zA-Z0-9\s]",  # Non-alphanumeric characters, often used in phishing
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, email_text, re.IGNORECASE):
            return True
    return False

def contains_suspicious_url(email_body):
    """Check if the email body contains suspicious URLs."""
    url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    urls = re.findall(url_pattern, email_body)
    
    suspicious_urls = [
        "example.com",  # Known suspicious URLs
        "phishingsite.com",
    ]
    
    for url in urls:
        for suspicious_url in suspicious_urls:
            if suspicious_url in url:
                return True
    return False



def process_email_prediction(ch, method, properties, body):
    """Process an email from RabbitMQ and push results to Kafka."""
    try:
        email = json.loads(body.decode())
        logger.info(f"Processing email with ID: {email['id']}")

        # Generate a cache key based on the email's sender and content
        cache_key = generate_cache_key(email)

        # Check if this email's prediction result is cached
        cached_result = redis_client.get(f"prediction:{cache_key}")
        
        if cached_result:
            # If the result is cached, log and send it to Kafka
            logger.info(f"Cache hit for email ID {email['id']}. Returning cached result.")
            result = json.loads(cached_result)
        else:
            # Otherwise, run the model inference
            email_text = f"Subject: {email['subject']} - {email['snippet']} - {email['body']}"
            
            # Perform inference
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
                        # Additional analysis (using BERT model or other analysis)
            # Additional analysis (using BERT model or other analysis)
            result["suspicious_sender"] = is_suspicious_sender(email['from'])
            result["suspicious_content"] = contains_suspicious_content(email['body'])
            result["suspicious_url"] = contains_suspicious_url(email['body'])

            # Cache the result in Redis
            redis_client.set(f"prediction:{cache_key}", json.dumps(result), ex=3600)  # Set TTL for 1 hour
            logger.info(f"Prediction result for email ID {email['id']} cached in Redis.")

        # Log and produce the result to Kafka
        logger.info(f"Prediction for email ID {email['id']} - Result: {result['predicted_label']}")
        kafka_producer = get_kafka_producer()
        kafka_producer.produce("detection_results_single", key=email['id'], value=json.dumps(result))
        kafka_producer.flush()

        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"Message with ID {email['id']} acknowledged and processed.")

    except Exception as e:
        logger.error(f"Error processing email: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

def start_prediction_service():
    """Start consuming messages from RabbitMQ."""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()

        # Declare the queue to ensure it exists
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

        channel.basic_qos(prefetch_count=1)  # Process one message at a time
        channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=process_email_prediction)

        logger.info("RabbitMQ prediction service started. Waiting for messages...")
        channel.start_consuming()

    except Exception as e:
        logger.error(f"Error starting RabbitMQ consumer: {e}")

if __name__ == "__main__":
    start_prediction_service()  # Start consuming from RabbitMQ
