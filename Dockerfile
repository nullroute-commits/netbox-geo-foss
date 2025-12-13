# Multi-stage Dockerfile for NetBox Geographic Data Integration
# Python 3.13.1
FROM python:3.13.1-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies for geographic libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libgeos-dev \
    libproj-dev \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy dependency files
COPY requirements/base.txt requirements/base.txt

# Create virtual environment and install dependencies
RUN python -m venv /app/.venv && \
    /app/.venv/bin/pip install --upgrade pip setuptools wheel && \
    /app/.venv/bin/pip install -r requirements/base.txt

# Stage 2: Runtime stage
FROM python:3.13.1-slim as runtime

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src:$PYTHONPATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgeos-c1v5 \
    libproj25 \
    libgdal34 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory and cache directory
WORKDIR /app
RUN mkdir -p /app/cache && chown -R appuser:appuser /app

# Copy Python dependencies from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser src /app/src
COPY --chown=appuser:appuser pyproject.toml /app/

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp && \
    chown -R appuser:appuser /app

# Install the package in editable mode
USER appuser
RUN /app/.venv/bin/pip install -e .

# Health check (simple Python check)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import netbox_geo; print(netbox_geo.__version__)" || exit 1

# Expose port (if running API server)
EXPOSE 8000

# Default command
CMD ["netbox-geo", "--help"]