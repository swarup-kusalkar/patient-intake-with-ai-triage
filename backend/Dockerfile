# syntax=docker/dockerfile:1
# =============================================================
# Backend Dockerfile — python:3.12-slim
# =============================================================

FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install curl for the healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements FIRST for Docker layer caching.
# This layer only rebuilds when requirements.txt changes — not on every code edit.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the application port
EXPOSE 8000

# Run Alembic migrations then start the server.
# alembic upgrade head is idempotent — safe to run on every startup.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
