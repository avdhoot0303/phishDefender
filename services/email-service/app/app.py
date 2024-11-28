import falcon
from app.api.auth_resource import AuthResource
from app.api.callback_resource import CallbackResource
from app.api.fetch_email_resource import FetchEmailsResource
from app.api.test_cors import TestCorsResource
import os 
from falcon_cors import CORS


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = "1"

# Initialize Falcon app

app = falcon.App(middleware=falcon.CORSMiddleware(
    allow_origins='*', expose_headers='*'))

# Register routes
app.add_route('/api/auth/login', AuthResource())  # Start OAuth flow
app.add_route('/api/auth/callback', CallbackResource())  # Handle OAuth callback
app.add_route('/api/fetch_emails', FetchEmailsResource())  # Make sure this is properly registered
# Define the route
app.add_route('/api/test-cors', TestCorsResource())
