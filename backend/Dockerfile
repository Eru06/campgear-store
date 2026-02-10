FROM python:3.11-slim AS base

# Prevent bytecode files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps for asyncpg and Pillow
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev libjpeg62-turbo-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r campgear && useradd -r -g campgear campgear && \
    mkdir -p /data/uploads && chown -R campgear:campgear /data/uploads

USER campgear

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
