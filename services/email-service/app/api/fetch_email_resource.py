# app/api/fetch_emails_resource.py

import falcon
import google
import os
import logging
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from app.config import TOKEN_STORE  # Token store for your app
from bs4 import BeautifulSoup  # For parsing HTML email body
import base64
from google_auth_oauthlib.flow import InstalledAppFlow

import json
# from app.kafka_producer import send_to_kafka

class FetchEmailsResource:
    def on_get(self, req, resp):
        """Fetch the user's Gmail messages."""
        # Add CORS headers to the response
        resp.set_header('Access-Control-Allow-Origin', '*')
        resp.set_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        resp.set_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

        user_id = "current_user"  # Replace with actual user identification logic
        tokens = TOKEN_STORE.get(user_id)

        if not tokens:
            raise falcon.HTTPUnauthorized(description="No tokens found for the user. Please authenticate first.")

        try:
            # credentials = get_credentials_from_gcs() #use credentials from GCS 
            # Rebuild credentials using the stored tokens
            credentials = Credentials(
                token=tokens['access_token'],  # access token
                refresh_token=tokens['refresh_token'],  # refresh token
                token_uri='https://oauth2.googleapis.com/token',
                client_id=os.environ.get('CLIENT_ID'),
                client_secret=os.environ.get('CLIENT_SECRET')
            )

            # If credentials are expired, refresh them
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

            # Use the credentials to build the Gmail API service
            service = build('gmail', 'v1', credentials=credentials)

            # Fetch the first 10 emails
            results = service.users().messages().list(userId='me', maxResults=10).execute()
            messages = results.get('messages', [])

            # Prepare the emails list
            emails = []
            for message in messages:
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                msg_dict = {
                    'id': msg['id'],
                    'snippet': msg.get('snippet', ''),  # Email preview snippet
                    'from': self.extract_header(msg, 'From'),
                    'subject': self.extract_header(msg, 'Subject'),
                    'date': self.extract_header(msg, 'Date'),
                }

                # Extract the body of the email
                msg_dict['body'] = self.extract_body(msg)

                emails.append(msg_dict)
                # send_to_kafka(msg_dict)  # Push each email to the Kafka topic

            # Respond with the fetched emails
            resp.media = {
                "status": "success",
                "emails": emails
            }

        except Exception as e:
            logging.error(f"Error fetching emails: {str(e)}")
            resp.status = falcon.HTTP_500
            resp.media = {
                "status": "error",
                "message": str(e)
            }

    def extract_header(self, message, header_name):
        """Helper method to extract headers like 'From', 'Subject', 'Date'."""
        headers = message['payload'].get('headers', [])
        for header in headers:
            if header['name'] == header_name:
                return header['value']
        return ''
    
    def extract_body(self, message):
        """Extract and decode the body of the email."""
        payload = message['payload']
        parts = payload.get('parts', [])

        # If there are parts (multipart email), we need to decode the right one
        for part in parts:
            if part['mimeType'] == 'text/plain':
                body_data = part['body'].get('data', '')
                if body_data:
                    # Decode the body from base64
                    decoded_body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                    return decoded_body
            elif part['mimeType'] == 'text/html':
                body_data = part['body'].get('data', '')
                if body_data:
                    # Decode the body from base64
                    decoded_body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                    soup = BeautifulSoup(decoded_body, "html.parser")
                    return soup.get_text()
        return "No Body Found"
    
    def get_credentials(self):
        """Fetch credentials from local or cloud storage (GCS or local)."""
        try:
            # Assuming the client_secrets.json file is present in the app folder
            # You can either download it from GCS or keep it in the local directory
            client_secrets_path = '/app/client_secrets.json'  # Adjust this path as needed
            if not os.path.exists(client_secrets_path):
                raise FileNotFoundError("client_secrets.json not found")

            with open(client_secrets_path, 'r') as file:
                credentials_info = json.load(file)

            # Use the credentials file to authenticate
            credentials = Credentials.from_authorized_user_info(info=credentials_info)

            # If credentials are invalid or expired, use the flow to authenticate
            if not credentials or credentials.expired:
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secrets_path, 
                    scopes=['https://www.googleapis.com/auth/gmail.readonly']
                )
                credentials = flow.run_local_server(port=0)

            return credentials
        except Exception as e:
            logging.error(f"Error loading credentials: {str(e)}")
            raise falcon.HTTPUnauthorized(description="Failed to authenticate with Google API.")
