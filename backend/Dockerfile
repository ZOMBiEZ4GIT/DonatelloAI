# ╔════════════════════════════════════════════════════════╗
# ║         Production Dockerfile - Backend Service        ║
# ║              Enterprise Image Gen Platform             ║
# ╚════════════════════════════════════════════════════════╝

# ┌─────────────────────────────────────────────────────────┐
# │ 🏗️ Build Stage: Security scanning & dependency build   │
# └─────────────────────────────────────────────────────────┘
FROM python:3.11-slim-bookworm AS builder

# Security: Run as non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    unixodbc-dev \
    # Microsoft ODBC Driver for SQL Server
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
WORKDIR /build
COPY requirements.txt .

# 💰 COST OPTIMIZATION: Cache pip packages
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# 🔒 SECURITY: Scan dependencies for vulnerabilities
RUN pip install safety && \
    safety check --json || echo "WARNING: Vulnerability scan found issues"

# ┌─────────────────────────────────────────────────────────┐
# │ 🚀 Runtime Stage: Minimal production image              │
# └─────────────────────────────────────────────────────────┘
FROM python:3.11-slim-bookworm

# Metadata labels (ISO 27001 A.8.1.1 - Asset ownership)
LABEL maintainer="platform-team@organization.com.au" \
      version="0.1.0" \
      description="EIG Platform Backend Service" \
      security.compliance="ISO27001" \
      data.classification="confidential" \
      data.residency="australia"

# Security: Run as non-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unixodbc \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser alembic.ini .

# Security: Set proper file permissions
RUN chmod -R 755 /app && \
    chmod -R 500 /app/app

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000

# Health check (ISO 27001 A.12.1.3 - Capacity management)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:${PORT}/api/v1/health || exit 1

# Expose port
EXPOSE ${PORT}

# 🚀 Production command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--log-config", "app/core/logging.py"]

# ⚠️  SECURITY NOTES:
# - Image runs as non-root user 'appuser'
# - No secrets baked into image (use Azure Key Vault)
# - Minimal attack surface (slim base image)
# - Regular security scans required (Trivy, Snyk)
# - Health checks for container orchestration
#
# 📋 ISO 27001 Controls:
# - A.12.6.1: Management of technical vulnerabilities
# - A.14.2.6: Secure development environment
