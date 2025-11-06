FROM python:3.12-slim

# Install system dependencies for document processing
RUN apt-get update && apt-get install -y \
    default-jre \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./src ./nextcloud-ingestor/

# Create a non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set the working directory to where main.py is located
WORKDIR /app/nextcloud-ingestor

# Run the application
CMD ["python", "main.py"]
