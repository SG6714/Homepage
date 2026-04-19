# Start with an official Python slim image for a smaller footprint
FROM python:3.9-slim

# Set the main application directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Ensure the persistent log directory exists
RUN mkdir -p /data


# Tell Docker that the container listens on port 5000
EXPOSE 5000

# NEW: Use Gunicorn to run the app in a production-ready way.
# This starts 4 worker processes to handle multiple simultaneous requests.
# It binds to port 5000 inside the container and looks for the Flask 'app' object in the '/app/app.py' file.
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "--chdir", "/app", "app:app"]