# syntax=docker/dockerfile:1
# Multi-stage Dockerfile for NetBox Geographic Data Integration
# Stages: base → builder → ci → production

# ── base: system dependencies ──────────────────────────────────────────────────
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libgeos-dev \
    libproj-dev \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── builder: production Python dependencies ────────────────────────────────────
FROM base AS builder

COPY requirements/base.txt requirements/base.txt
RUN python -m venv /app/.venv && \
    /app/.venv/bin/pip install --upgrade pip setuptools wheel && \
    /app/.venv/bin/pip install -r requirements/base.txt

# ── ci: dev dependencies + source (for lint/test in Docker) ───────────────────
FROM builder AS ci

COPY requirements/dev.txt requirements/dev.txt
RUN /app/.venv/bin/pip install -r requirements/dev.txt

COPY pyproject.toml .
COPY src src/
COPY tests tests/
RUN /app/.venv/bin/pip install -e . --no-deps

ENV PATH="/app/.venv/bin:$PATH" \
    CI=true

# Default: run the test suite
CMD ["pytest", "--cov=netbox_geo", "--cov-report=term-missing", "-v"]

# ── production: slim runtime image ────────────────────────────────────────────
FROM python:3.12-slim AS production

# Geo runtime libraries only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgeos-c1v5 \
    libproj25 \
    gdal-bin \
    libgdal36 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy only the pre-built venv from builder
COPY --from=builder /app/.venv /app/.venv

# Create writable directories before dropping privileges
RUN mkdir -p /app/cache /app/logs && chown -R appuser:appuser /app

COPY --chown=appuser:appuser pyproject.toml .
COPY --chown=appuser:appuser src src/

USER appuser
RUN /app/.venv/bin/pip install -e . --no-deps --no-build-isolation

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import netbox_geo; print(netbox_geo.__version__)" || exit 1

EXPOSE 8000
CMD ["netbox-geo", "--help"]
