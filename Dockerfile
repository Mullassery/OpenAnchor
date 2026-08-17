# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY pyproject.toml setup.py ./
RUN pip install --user --no-cache-dir --upgrade pip && \
    pip install --user --no-cache-dir .

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Set environment variables
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy application code
COPY openanchor /app/openanchor
COPY tests /app/tests

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -m openanchor health || exit 1

# Default command: run the built-in health server so the container has a
# real foreground process. 0.0.0.0 is intentional here (bind-all is the
# correct default *inside* a container network namespace); this is
# unrelated to the MCP connector's host binding, which defaults to
# loopback-only (see openanchor/_mcp_connector.py).
CMD ["python", "-m", "openanchor", "serve", "--host", "0.0.0.0", "--port", "8080"]
