FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmagic1 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire backend app
COPY backend/ .

# Create storage dirs
RUN mkdir -p /app/storage/uploads /app/storage/outputs /app/storage/temp

RUN useradd -m -u 1001 worker && chown -R worker:worker /app
USER worker

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD celery -A app.celery_app inspect ping -t 5 || exit 1

CMD ["celery", "-A", "app.celery_app", "worker", \
     "--loglevel=info", \
     "--concurrency=2", \
     "--queues=celery", \
     "--max-tasks-per-child=200"]
