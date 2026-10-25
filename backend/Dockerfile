# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (ffmpeg and ffprobe required for finalization merges)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

# Expose the port Render expects
EXPOSE 8000

# Run Uvicorn via shell to bind to Render's dynamic PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
