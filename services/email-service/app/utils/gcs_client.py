# # app/utils/gcs_client.py

# import os
# from google.cloud import storage
# from google.oauth2.credentials import Credentials
# from google.auth.transport.requests import Request
# import json

# def download_secrets_from_gcs(bucket_name, file_name, destination_path):
#     """Download client_secrets.json from Google Cloud Storage to the local filesystem."""
#     client = storage.Client()  # Initialize a GCS client
#     bucket = client.get_bucket(bucket_name)  # Reference the bucket
#     blob = bucket.blob(file_name)  # Reference the specific file

#     # Download the file to the local path (temporary location)
#     blob.download_to_filename(destination_path)
#     print(f"Downloaded {file_name} from GCS to {destination_path}")

# def get_credentials_from_gcs():
#     """Download client_secrets.json from GCS and return the credentials."""
#     bucket_name = 'secret_bucket_ams_560'  # Replace with your GCS bucket name
#     file_name = 'client_secrets.json'  # This is the file you want to download
#     destination_path = '/tmp/client_secrets.json'  # Temporary file path (Cloud Run)

#     # Download the file from GCS to the local filesystem
#     download_secrets_from_gcs(bucket_name, file_name, destination_path)

#     # Load the credentials from the downloaded file
#     with open(destination_path, 'r') as file:
#         credentials_info = json.load(file)

#     return credentials_info