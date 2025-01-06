# app/api/auth_resource.py
import falcon
import logging
from google_auth_oauthlib.flow import Flow
from app.auth import SCOPES

class AuthResource:
    """Handle the OAuth login flow."""
    def on_get(self, req, resp):
        """Start the OAuth flow and redirect to Google authorization."""
        logging.info("Starting the OAuth login flow")

        flow = Flow.from_client_secrets_file('client_secrets.json', ' '.join(SCOPES))
        flow.redirect_uri = 'https://email-service-210145104871.us-central1.run.app/api/auth/callback'  # Ensure this URI matches Google Console

        # Generate authorization URL
        authorization_url, state = flow.authorization_url( prompt='consent')

        logging.info(f"Redirecting user to: {authorization_url}")
        
        resp.status = falcon.HTTP_302
        resp.location = authorization_url
        resp.set_header('Location', authorization_url)


    def on_options(self, req, resp):
        # Handle preflight CORS requests
        resp.status = falcon.HTTP_200
        resp.set_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        resp.set_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        resp.set_header('Access-Control-Allow-Origin', '*')
