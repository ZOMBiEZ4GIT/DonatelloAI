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

from typing import Dict, Any
from fastapi import APIRouter, status
from pydantic import BaseModel

from app.core.config import settings

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
    # TODO: Add actual health checks
    # - Database connectivity
    # - Redis connectivity
    # - Azure Key Vault accessibility
    # - Model provider APIs accessibility
    # - Disk space availability
    # - Memory usage

    checks = {
        "application": "healthy",
        # "database": "healthy",  # TODO: Implement
        # "redis": "healthy",  # TODO: Implement
        # "key_vault": "healthy",  # TODO: Implement
    }

    # Determine overall status
    overall_status = "healthy" if all(v == "healthy" for v in checks.values()) else "unhealthy"

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
    # TODO: Add actual readiness checks
    # - Database connection pool has available connections
    # - Redis is accessible
    # - Azure Key Vault is accessible
    # - Minimum memory available

    return {"status": "ready"}


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
