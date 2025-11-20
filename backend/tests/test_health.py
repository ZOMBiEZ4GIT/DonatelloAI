"""
Tests for health check endpoints.
"""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_liveness_probe():
    """Test liveness probe endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/health/liveness")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test main health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    # Health check may fail if dependencies aren't available
    # Just verify the endpoint exists and returns proper structure
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "environment" in data
    assert "checks" in data
