FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Create necessary directories
RUN mkdir -p data .files

# Make scripts executable
RUN chmod +x scripts/*.py

EXPOSE 8000 8001

# Default command (can be overridden in docker-compose)
CMD ["python", "scripts/start_server.py"]

