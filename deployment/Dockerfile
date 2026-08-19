# AHOS Production Container Image
FROM python:3.11-slim AS base

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

# Install core python dependencies.
# No `|| fallback`: if requirements.txt cannot install, the build MUST fail
# loudly rather than silently producing an image with the wrong packages.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . /app

# Create non-root runtime user. chmod runs BEFORE the USER switch so it is
# guaranteed to succeed regardless of the git checkout's file mode.
RUN useradd -m -u 1000 ahosuser && \
    chmod +x /app/deployment/entrypoint.sh && \
    mkdir -p /app/data /app/reports && \
    chown -R ahosuser:ahosuser /app

USER ahosuser

# Healthcheck probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 /app/deployment/healthcheck.py || exit 1

EXPOSE 8000

ENTRYPOINT ["/app/deployment/entrypoint.sh"]
CMD ["python3", "-m", "architecture.runtime"]
