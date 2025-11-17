"""
╔════════════════════════════════════════════════════════╗
║              Health Check Endpoint                      ║
║         Kubernetes Liveness/Readiness Probes           ║
╚════════════════════════════════════════════════════════╝

Business Context:
    - Used by Azure Kubernetes Service for health monitoring
    - Determines if container should receive traffic
    - Triggers automatic pod restarts on failure

ISO 27001 Control: A.12.1.3 - Capacity management
"""

import asyncio
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.db.session import get_engine

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    environment: str
    checks: Dict[str, Any]


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="""
    Health check endpoint for monitoring and orchestration.

    **Used by:**
    - Kubernetes liveness/readiness probes
    - Azure Front Door health checks
    - Monitoring systems
    - Load balancers

    **Checks:**
    - Application is running
    - Dependencies are accessible (TODO)
    - No critical errors

    **ISO 27001 Control:** A.12.1.3 - Capacity management
    """,
    tags=["health"],
)
async def health_check() -> HealthResponse:
    """
    Perform health check.

    Returns:
        HealthResponse: Current health status

    Notes:
        - Returns 200 OK if healthy
        - Returns 503 Service Unavailable if unhealthy
        - No authentication required
        - Excluded from audit logging
    """
    checks = {}

    # Application check (always healthy if code is running)
    checks["application"] = "healthy"

    # Database check
    checks["database"] = await _check_database()

    # Redis check
    checks["redis"] = await _check_redis()

    # Determine overall status
    overall_status = "healthy" if all(v == "healthy" for v in checks.values()) else "unhealthy"

    # Return 503 if unhealthy
    status_code = status.HTTP_200_OK if overall_status == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

    if overall_status != "healthy":
        logger.warning("health_check_failed", checks=checks)
        raise HTTPException(status_code=status_code, detail=checks)

    return HealthResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        checks=checks,
    )


@router.get(
    "/health/liveness",
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description="""
    Kubernetes liveness probe endpoint.

    Indicates whether the application is running.
    If this fails, Kubernetes will restart the pod.

    **Simple check:** Is the application process alive?
    """,
    tags=["health"],
    include_in_schema=False,  # Hide from API docs
)
async def liveness_probe() -> Dict[str, str]:
    """
    Liveness probe for Kubernetes.

    Returns:
        Simple status indicating application is alive
    """
    return {"status": "alive"}


@router.get(
    "/health/readiness",
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
    description="""
    Kubernetes readiness probe endpoint.

    Indicates whether the application is ready to serve traffic.
    If this fails, Kubernetes will remove the pod from the service.

    **Checks:**
    - Database connections available
    - Critical dependencies accessible
    """,
    tags=["health"],
    include_in_schema=False,  # Hide from API docs
)
async def readiness_probe() -> Dict[str, str]:
    """
    Readiness probe for Kubernetes.

    Returns:
        Status indicating application is ready

    Notes:
        - Returns 200 if ready to serve traffic
        - Returns 503 if not ready (dependencies unavailable)
    """
    # Check critical dependencies
    db_status = await _check_database()
    redis_status = await _check_redis()

    if db_status != "healthy" or redis_status != "healthy":
        logger.warning("readiness_check_failed", database=db_status, redis=redis_status)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "database": db_status, "redis": redis_status},
        )

    return {"status": "ready"}


# ┌─────────────────────────────────────────────────────────┐
# │ Internal Health Check Functions                         │
# └─────────────────────────────────────────────────────────┘


async def _check_database() -> str:
    """
    Check database connectivity.

    Returns:
        "healthy" if database is accessible, "unhealthy" otherwise
    """
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            # Simple SELECT 1 query with timeout
            await asyncio.wait_for(
                conn.execute(text("SELECT 1")),
                timeout=5.0,
            )
        return "healthy"
    except asyncio.TimeoutError:
        logger.error("database_health_check_timeout")
        return "unhealthy"
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return "unhealthy"


async def _check_redis() -> str:
    """
    Check Redis connectivity.

    Returns:
        "healthy" if Redis is accessible, "unhealthy" otherwise
    """
    try:
        redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        # PING command with timeout
        await asyncio.wait_for(redis.ping(), timeout=5.0)
        await redis.close()
        return "healthy"
    except asyncio.TimeoutError:
        logger.error("redis_health_check_timeout")
        return "unhealthy"
    except Exception as e:
        logger.error("redis_health_check_failed", error=str(e))
        return "unhealthy"


# ⚠️  HEALTH CHECK NOTES:
#
# 🏥 Kubernetes Probes:
# - Liveness: Is the application running? (restart if fails)
# - Readiness: Can it serve traffic? (remove from service if fails)
# - Startup: Has it finished starting? (delay liveness/readiness)
#
# 📊 Recommended Probe Configuration:
# livenessProbe:
#   httpGet:
#     path: /api/v1/health/liveness
#     port: 8000
#   initialDelaySeconds: 30
#   periodSeconds: 10
#   timeoutSeconds: 5
#   failureThreshold: 3
#
# readinessProbe:
#   httpGet:
#     path: /api/v1/health/readiness
#     port: 8000
#   initialDelaySeconds: 10
#   periodSeconds: 5
#   timeoutSeconds: 3
#   failureThreshold: 2
#
# 📋 ISO 27001 Control: A.12.1.3 - Capacity management
