# app/config.py
import os 
import json

TOKEN_FILE = 'tokens.json'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CLIENT_SECRET_FILE = 'client_secret.json'  # Path to your OAuth client secret file
TOKEN_FILE = 'storage.json'  # File to store tokens
TOKEN_STORE = {}

# Load tokens from a file
def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as file:
            return json.load(file)
    return {}

# Save tokens to a file
def save_tokens(tokens):
    with open(TOKEN_FILE, 'w') as file:
        json.dump(tokens, file)
