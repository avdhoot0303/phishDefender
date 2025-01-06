# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000 to access the service locally
EXPOSE 8001

# Run prediction service when the container launches
CMD ["python", "prediction_service.py"]
