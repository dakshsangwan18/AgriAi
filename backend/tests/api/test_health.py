"""
Tests for health check endpoints.

Tests cover:
- Basic health check
- Database pool status
- Readiness probe
- Liveness probe
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    
    def test_basic_health_check(self, client: TestClient):
        response = client.get("/api/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "AgriAI Platform API"
    
    def test_readiness_probe(self, client: TestClient):
        response = client.get("/api/health/ready")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data
        assert data["checks"]["database"] == "ok"
    
    def test_liveness_probe(self, client: TestClient):
        response = client.get("/api/health/live")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "alive"
    
    def test_db_pool_status(self, client: TestClient, admin_headers):
        response = client.get("/api/health/db-pool", headers=admin_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check status and pool data are present
        assert "status" in data
        assert "pool" in data
        
        # Pool statistics should be present
        pool = data["pool"]
        assert "type" in pool or "size" in pool
        
        # Recommendations should be present
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)
