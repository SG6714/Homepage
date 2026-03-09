# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first (optimizes Docker caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port Flask/Gunicorn will run on
EXPOSE 5000

# Run the app using Gunicorn
# -b 0.0.0.0:5000 binds it to all network interfaces
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
