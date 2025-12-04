"""Tests for health check endpoints."""

from fastapi.testclient import TestClient


class TestPublicHealthEndpoint:
    """Tests for the public /health endpoint."""

    def test_health_returns_200(self, client: TestClient):
        """Test public health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self, client: TestClient):
        """Test health endpoint returns JSON content type."""
        response = client.get("/health")
        assert "application/json" in response.headers.get("content-type", "")

    def test_health_contains_status(self, client: TestClient):
        """Test health response contains status field."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_contains_app_name(self, client: TestClient):
        """Test health response contains app name."""
        response = client.get("/health")
        data = response.json()
        assert "app" in data


class TestAPIHealthEndpoint:
    """Tests for the /api/data/health endpoint."""

    def test_api_health_returns_200(self, client: TestClient):
        """Test /api/data/health returns 200."""
        response = client.get("/api/data/health")
        assert response.status_code == 200

    def test_api_health_returns_json(self, client: TestClient):
        """Test /api/data/health returns JSON."""
        response = client.get("/api/data/health")
        assert "application/json" in response.headers.get("content-type", "")

    def test_api_health_contains_status(self, client: TestClient):
        """Test response contains status field."""
        response = client.get("/api/data/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_api_health_contains_database_status(self, client: TestClient):
        """Test response contains database_initialized field."""
        response = client.get("/api/data/health")
        data = response.json()
        assert "database_initialized" in data
        assert isinstance(data["database_initialized"], bool)
