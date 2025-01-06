from app import PredictSingle, PredictBatch
import falcon
from waitress import serve
from app import consume_messages, read_config

# Initialize Falcon app
app = falcon.App()

# Add routes
app.add_route('/api/predict/single', PredictSingle())
app.add_route('/api/predict/batch', PredictBatch())





# For local testing, run with Waitress server
if __name__ == "__main__":
    kafka_config = read_config()
    messages = consume_messages(kafka_config)
    
    print("Starting server at http://127.0.0.1:8000")
    serve(app, host='127.0.0.1', port=8000)
