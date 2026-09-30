# =================================================================
# Kestrel Core API — Multi-Stage Production Dockerfile
# Hardened, Non-Root, Minimal Attack Surface
# =================================================================

# ----------------- Stage 1: Build Dependencies ------------------
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ----------------- Stage 2: Production Runtime -------------------
FROM python:3.11-slim AS runner

WORKDIR /app

# Install runtime utilities only (curl for container healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Create non-root system user and group (kestrel: 10001)
RUN groupadd -g 10001 kestrel && \
    useradd -u 10001 -g kestrel -s /bin/bash -m kestrel

# Copy application source code
COPY . .

# Set permissions for uploads, logs, and cache
RUN mkdir -p /app/uploads && \
    chown -R kestrel:kestrel /app

USER kestrel

EXPOSE 8000

# Docker native healthcheck against Kestrel Core Health API
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Production WSGI/ASGI server invocation
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers"]
