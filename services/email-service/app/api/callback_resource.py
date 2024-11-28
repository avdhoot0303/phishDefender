# app/api/callback_resource.py
import falcon
import logging
from app.auth import exchange_code_for_credentials
from app.config import TOKEN_STORE  # Token store (in-memory storage)
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

class CallbackResource:
    """Handle the OAuth callback after user login."""
    def on_get(self, req, resp):
        """Exchange the authorization code for credentials."""
        authorization_code = req.get_param('code')

        if not authorization_code:
            logging.error("Authorization code is missing.")
            resp.status = falcon.HTTP_400
            resp.media = {"error": "Authorization code is missing"}
            return

        try:
            # Exchange the authorization code for credentials (tokens)
            credentials = exchange_code_for_credentials(authorization_code)

            # Store the tokens in the TOKEN_STORE (in-memory or persistent storage)
            user_id = "current_user"  # You should use an actual user ID here
            TOKEN_STORE[user_id] = {
                "access_token": credentials.get('access_token'),
                "refresh_token": credentials.get('refresh_token'),
                "token_expiry": credentials.get('expires_at')
            }

            # Respond with the tokens (for testing purposes)
            # resp.status = falcon.HTTP_200
            # resp.media = {
            #     "status": "success",
            #     "access_token": credentials.get('access_token'),
            #     "refresh_token": credentials.get('refresh_token'),
            #     "token_expiry": credentials.get('expires_at')
            # }
            # Instead of sending the tokens directly, redirect to the frontend's email page
            resp.status = falcon.HTTP_302  # HTTP Redirect
        
            resp.set_header('Location', f"http://localhost:3000/setToken?token={credentials.get('access_token')}")  # Redirect to frontend's email page
            return

        except Exception as e:
            logging.error(f"Error during callback: {e}")
            resp.status = falcon.HTTP_500
            resp.media = {"error": str(e)}
