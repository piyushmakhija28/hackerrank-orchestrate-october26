# Multi-Stage Secure Production Dockerfile
# Base Image: Python 3.13 Slim
# Security: Non-Root Execution, Minimal Attack Surface

# Stage 1: Build Dependencies
FROM python:3.13-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: Minimal Runtime
FROM python:3.13-slim AS runtime

WORKDIR /app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

COPY --from=builder /opt/venv /opt/venv

COPY code/ ./code/
COPY README.md .
COPY AGENTS.md .

RUN chown -R appuser:appgroup /app

USER appuser

ENTRYPOINT ["python", "code/main.py"]
CMD ["--requests", "dataset/deletion_requests.csv", "--output", "output.csv"]
