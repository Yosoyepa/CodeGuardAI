# ==========================================
# CodeGuard AI - Backend Dockerfile
# Python 3.11 + FastAPI
# Optimized for Google Cloud Run
# ==========================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="CodeGuard AI Team <team@codeguard.com>"
LABEL description="Multi-Agent Code Review System - Backend API"

# Environment variables for Python optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Cloud Run uses PORT env variable
    PORT=8080

# Set working directory
WORKDIR /app

# Install system dependencies (minimal for Cloud Run)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user (Cloud Run best practice)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Cloud Run will set PORT dynamically, expose default
EXPOSE 8080

# Cloud Run handles health checks via HTTP, no HEALTHCHECK needed
# Use shell form to allow $PORT expansion at runtime
CMD uvicorn src.main:app --host 0.0.0.0 --port $PORT
