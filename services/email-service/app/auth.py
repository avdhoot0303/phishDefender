import logging
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

CLIENT_SECRETS_FILE = 'client_secrets.json'
REDIRECT_URI = 'https://email-service-210145104871.us-central1.run.app/api/auth/callback'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def exchange_code_for_credentials(authorization_code):
    """Exchange the authorization code for credentials."""
    logging.info("Exchanging authorization code for credentials.")
    
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    flow.redirect_uri = REDIRECT_URI  # Ensure this matches exactly the URI in the Google Cloud Console
    try:
        credentials = flow.fetch_token(code=authorization_code)
        
        logging.info("Credentials successfully obtained.")
        return credentials
    except Exception as e:
        logging.error(f"Error during code exchange: {str(e)}")
        raise Exception("Error exchanging code for credentials")
    
def get_user_info(credentials):
    """Retrieve the user's info using the OAuth credentials."""
    logging.info("Fetching user info from Google API.")
    try:
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        logging.info(f"User info fetched: {user_info}")
        return user_info
    except Exception as e:
        logging.error(f"Error retrieving user info: {str(e)}")
        raise Exception("Error retrieving user info")
