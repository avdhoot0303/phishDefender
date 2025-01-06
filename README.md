
# Phishing Detection System



This system leverages multiple components such as Kafka, RabbitMQ, Redis, and a BERT model to perform phishing detection on emails, SMS, URLs, and websites. The system consists of two main backend services: **email-service** (deployed on Cloud Run) and **ml-service** (running locally or in Docker). It also provides a frontend built in React to interact with the phishing detection system.
## Integrating Google Authentication

This document outlines how to integrate Google Authentication into the phishing detection system for secure user access.

**Requirements:**

  * A Google Cloud Project with APIs enabled
  * A Google Cloud service account with necessary permissions

**Steps:**

1.  **Enable Google Sign-In API:**

      - Navigate to the Google Cloud Console ([console.cloud.google.com](https://www.google.com/url?sa=E&source=gmail&q=https://www.google.com/url?sa=E%26source=gmail%26q=https://console.cloud.google.com/)) and select your project.
      - Go to "APIs & Services" -\> "Library".
      - Search for "Google Sign-In API" and enable it.

2.  **Create OAuth Client ID:**

      - Go to "APIs & Services" -\> "Credentials".
      - Click "Create credentials" and select "OAuth client ID".
      - Choose "Web application" as the application type.
      - Enter a name for your client (e.g., "Phishing Detection Frontend") and provide authorized redirect URIs:
          - `http://localhost:3000/auth/google/callback` (for local development)
          - The actual redirect URI for your deployed frontend (e.g., `https://your-domain.com/auth/google/callback`)

3.  **Configure Consent Screen:**

      - In the "Credentials" section, click on your newly created client ID.
      - Go to the "OAuth consent screen" tab.
      - Configure the following details:
          - **Authorized domain:** Your application's domain (e.g., `your-domain.com`)
          - **App logo:** Upload a logo for your application.
          - **Privacy Policy URI:** Provide a link to your application's privacy policy.
          - **Terms of Service URI:** Provide a link to your application's terms of service.

4.  **Download Client Secret:**

      - In the "Credentials" section, click on the download icon next to your client ID.
      - Choose "JSON" format and download the file securely. This file contains the client secret, which should be kept confidential.

5.  **Update Frontend Code:**

      - Modify your frontend code to integrate with the Google Sign-In API using the obtained client ID and redirect URI.
      - Upon successful login, the Google Sign-In API will redirect the user to your specified redirect URI with an authorization code.
      - Your frontend code should then exchange this code for an access token using the Google OAuth2 library.
      - Store the access token securely for future API calls. (**Note:** Implement proper security measures to protect the access token.)

**Additional Notes:**

  - Consider implementing refresh tokens to maintain long-term user sessions.
  - Refer to the Google Sign-In API documentation for detailed instructions and code examples: [https://developers.google.com/identity/gsi/web/reference/js-reference](https://www.google.com/url?sa=E&source=gmail&q=https://developers.google.com/identity/gsi/web/reference/js-reference)


## Prerequisites

Before starting the system, make sure you have the following components set up:

1. **Kafka**: Set up a local or remote Confluent Kafka cluster.  
   - **Note**: This project uses **Kafka on the cloud**, so you'll need to update Kafka configuration to connect to your cloud-based Kafka instance. The code may contain hardcoded references for Kafka.

2. **RabbitMQ**: Set up RabbitMQ locally (default port: `5672`).
   - You can run RabbitMQ locally using Docker:
     ```bash
     docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
     ```
   - Access RabbitMQ Management UI via [http://localhost:15672](http://localhost:15672) (Default login: `guest/guest`).

3. **Redis**: Set up Redis locally (default port: `6379`).
   - You can run Redis locally using Docker:
     ```bash
     docker run -d --name redis -p 6379:6379 redis
     ```

4. **Google Cloud**: If deploying the **email-service** to **Cloud Run**, ensure you have set up Google Cloud SDK and authenticated:
   ```bash
   gcloud auth login
   gcloud config set project [YOUR_PROJECT_ID]
   ```

---

## Backend Setup

### 1. **Email-Service** (Deployed on Cloud Run)

**Dockerfile**:
```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable for the Cloud Run service
ENV PORT=8080

# Run email service when the container launches
CMD ["python", "email_service.py"]
```

**Steps to run**:
1. Build the Docker image:
   ```bash
   docker build -t email-service .
   ```

2. Deploy to **Google Cloud Run**:
   ```bash
   gcloud run deploy email-service --image gcr.io/[YOUR_PROJECT_ID]/email-service --platform managed --region [YOUR_REGION] --allow-unauthenticated
   ```

### 2. **ML-Service** (Running locally with Docker)

To run the **ML-Service** in Docker, create a **Dockerfile**.

**Dockerfile**:
```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8001 to access the service locally
EXPOSE 8001

# Run prediction service when the container launches
CMD ["python", "prediction_service.py"]
```

**Steps to run**:
1. Build the Docker image for **ml-service**:
   ```bash
   docker build -t ml-service .
   ```

2. Run the container:
   ```bash
   docker run -p 8001:8001 ml-service
   ```

### 3. **Running the Services Locally**

1. Ensure **Kafka**, **RabbitMQ**, and **Redis** are running locally before starting the services.
2. Make sure the Kafka service is running, and your environment variables in the code are pointing to the correct local Kafka instance (`localhost:9092`).
3. RabbitMQ and Redis should be available at their default ports.

---

## Frontend Setup

**1. Install Node.js & npm**:
   - Ensure you have **Node.js** and **npm** installed:
     ```bash
     node -v
     npm -v
     ```

   - If not, download and install Node.js from [https://nodejs.org/](https://nodejs.org/).

**2. Set up the React App**:
   - Clone or download the frontend repo.
   - Inside the project folder, run the following commands:
     ```bash
     npm install   # Install all dependencies
     npm start     # Start the React app on localhost:3000
     ```

---

## Running the Entire System

1. **Kafka Topics**: Make sure you have created the necessary Kafka topics:
   - `emails-topic`: Topic to stream emails.
   - `detection_results`: Topic to push detection results.

   You can create the topics with the following Kafka commands:
   ```bash
   kafka-topics --create --topic emails-topic --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
   kafka-topics --create --topic detection_results --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
   ```

2. **Environment Variables**: Ensure your environment variables, including Kafka, RabbitMQ, Redis, and Google Cloud credentials, are correctly set in the code.

---

### Final Remarks

- **Kafka Topics**: Ensure that the Kafka topics (`emails-topic`, `detection_results`) are created.
- **Environment Variables**: Check that environment variables for Kafka, RabbitMQ, and Redis are properly set.
- **Cloud Deployment**: For production environments, the **email-service** is deployed on **Google Cloud Run**. The **ml-service** can be run locally or in a containerized environment.

---

### Troubleshooting

- If you encounter issues connecting to **Kafka** or **RabbitMQ**, ensure that the services are running and that the **environment variables** point to the correct addresses.
- If running locally, make sure the required ports (e.g., `9092` for Kafka, `5672` for RabbitMQ, `6379` for Redis) are not blocked by a firewall.

---
**Remember:**

  - This guide provides a general overview. Adjust the steps according to your specific backend framework and chosen frontend technology.
  - Securely store the client secret and access tokens.



