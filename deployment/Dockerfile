# AHOS Production Container Image
FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    AHOS_HOME=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install core python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt || pip install pytest pyyaml requests anyio

# Copy application source
COPY . /app

# Create non-root runtime user
RUN useradd -m -u 1000 ahosuser && \
    chown -R ahosuser:ahosuser /app

USER ahosuser

# Healthcheck probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 /app/deployment/healthcheck.py || exit 1

EXPOSE 8000

CMD ["python3", "-m", "architecture.runtime"]
