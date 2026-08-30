FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port
EXPOSE 8080

# Run alembic migrations and start uvicorn
CMD ["sh", "-c", "PYTHONPATH=. alembic upgrade head && PYTHONPATH=. uvicorn api.main:app --host 0.0.0.0 --port 8080"]
