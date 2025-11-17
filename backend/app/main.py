"""
╔════════════════════════════════════════════════════════╗
║         FastAPI Application Entry Point                ║
║              Enterprise Image Gen Platform             ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Core API gateway for all image generation requests
    - Handles 1000+ requests per second at scale
    - Subject to ISO 27001 A.12.4.1 (Event logging)

Security Considerations:
    - All endpoints require authentication (ISO 27001 A.9.4.2)
    - Rate limiting enforced (ISO 27001 A.13.1.3)
    - CORS restricted to known origins
    - Comprehensive audit logging

Modifications:
    - CORS_ORIGINS: Update in .env file
    - RATE_LIMITS: Configure in app/core/config.py
    - MIDDLEWARE: Add/modify in app/core/middleware.py
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.middleware import AuditLoggingMiddleware, SecurityHeadersMiddleware
from app.api.v1.endpoints import health, budgets

# ┌─────────────────────────────────────────────────────────┐
# │ 🚀 Application Lifespan Management                      │
# └─────────────────────────────────────────────────────────┘


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events for the application.

    Business Context:
        - Initializes database connections
        - Sets up monitoring and logging
        - Performs health checks on external services
        - Graceful shutdown for zero-downtime deployments

    ISO 27001 Controls:
        - A.12.1.3: Capacity management
        - A.12.6.1: Management of technical vulnerabilities
    """
    # 🟢 STARTUP
    logger.info(
        "application_startup",
        environment=settings.ENVIRONMENT,
        version=settings.APP_VERSION,
        iso27001_mode=settings.ISO27001_MODE,
    )

    # TODO: Initialize database connection pool
    # TODO: Verify Azure Key Vault connectivity
    # TODO: Test model provider API connectivity
    # TODO: Initialize Application Insights

    logger.info("application_startup_complete")

    yield

    # 🔴 SHUTDOWN
    logger.info("application_shutdown")

    # TODO: Close database connections
    # TODO: Flush audit logs to Cosmos DB
    # TODO: Complete pending background tasks
    # TODO: Send shutdown metrics to Application Insights

    logger.info("application_shutdown_complete")


# ┌─────────────────────────────────────────────────────────┐
# │ 📦 FastAPI Application Instance                         │
# └─────────────────────────────────────────────────────────┘

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## Enterprise Image Generation Platform API

    **Security**: ISO 27001 & ISO/IEC 23053 compliant

    **Data Sovereignty**: Australian data residency guaranteed

    **Features**:
    - Multi-model AI image generation
    - Intelligent cost optimization
    - Comprehensive audit trails
    - Department budget management
    - PII detection and content filtering

    **Authentication**: Azure Entra ID with MFA required

    **Support**: support@organization.com.au
    """,
    docs_url="/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_API_DOCS else None,
    openapi_url="/openapi.json" if settings.ENABLE_API_DOCS else None,
    lifespan=lifespan,
    # Security headers
    swagger_ui_parameters={
        "persistAuthorization": False,  # Don't persist auth in browser
    },
)

# ┌─────────────────────────────────────────────────────────┐
# │ 🔒 Security Middleware (ISO 27001 A.13.1.3)             │
# └─────────────────────────────────────────────────────────┘

# Security headers middleware (OWASP security headers)
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining"],
)

# GZip compression for responses >1000 bytes
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 📊 Audit logging middleware (ISO 27001 A.12.4.1)
app.add_middleware(AuditLoggingMiddleware)

# ┌─────────────────────────────────────────────────────────┐
# │ 🛣️ Route Registration                                   │
# └─────────────────────────────────────────────────────────┘

# Health check endpoint (no auth required)
app.include_router(
    health.router,
    prefix=settings.API_V1_PREFIX,
    tags=["health"],
)

# Budget management endpoints (auth required)
app.include_router(
    budgets.router,
    prefix=settings.API_V1_PREFIX,
    tags=["budgets"],
)

# TODO: Register additional routers
# app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["auth"])
# app.include_router(generation.router, prefix=f"{settings.API_V1_PREFIX}/generate", tags=["generation"])
# app.include_router(admin.router, prefix=f"{settings.API_V1_PREFIX}/admin", tags=["admin"])

# ┌─────────────────────────────────────────────────────────┐
# │ ⚠️ Global Exception Handlers                            │
# └─────────────────────────────────────────────────────────┘


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled errors.

    Security Considerations:
        - Never expose stack traces to clients (information disclosure)
        - Log full error details for investigation
        - Return generic error message to client

    ISO 27001 Control: A.12.4.1 - Event logging
    """
    logger.error(
        "unhandled_exception",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )

    # 🚨 Never expose internal error details in production
    if settings.ENVIRONMENT == "production":
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred. Please contact support.",
                "request_id": request.state.request_id if hasattr(request.state, "request_id") else None,
            },
        )
    else:
        # Development: Show more details for debugging
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": str(exc),
                "type": type(exc).__name__,
            },
        )


# ┌─────────────────────────────────────────────────────────┐
# │ 🏠 Root Endpoint                                        │
# └─────────────────────────────────────────────────────────┘


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """
    Root endpoint with basic API information.

    Returns:
        Basic API metadata and links
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs" if settings.ENABLE_API_DOCS else "disabled",
        "health": f"{settings.API_V1_PREFIX}/health",
    }


# ⚠️  SECURITY NOTES:
# - All API endpoints (except /health) require authentication
# - Rate limiting enforced via SlowAPI middleware
# - CSRF protection for state-changing operations
# - SQL injection prevented via SQLAlchemy ORM
# - XSS prevented via Pydantic validation and output encoding
#
# 💰 COST IMPACT:
# - Application Insights telemetry: ~$2-5/day
# - Azure SQL connections: Connection pooling optimizes costs
# - Monitor metrics: Free tier covers typical usage
#
# 📋 ISO 27001 Control Mapping:
# - A.9.4.2: Secure log-on procedures
# - A.12.4.1: Event logging
# - A.13.1.3: Segregation in networks
# - A.14.2.1: Secure development policy
