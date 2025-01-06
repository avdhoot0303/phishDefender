# redis_cache.py

import redis
import json

# Connect to Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

def cache_prediction(email_id, result):
    """Cache the prediction result in Redis."""
    redis_client.set(f"prediction:{email_id}", json.dumps(result), ex=3600)  # Set TTL for 1 hour

def get_cached_prediction(email_id):
    """Get the cached prediction result from Redis."""
    cached_result = redis_client.get(f"prediction:{email_id}")
    return json.loads(cached_result) if cached_result else None
