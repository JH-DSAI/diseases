"""Tests for API endpoints"""

import pytest
from fastapi.testclient import TestClient


def test_public_health_endpoint(unauthenticated_client: TestClient):
    """Test public health endpoint doesn't require auth"""
    response = unauthenticated_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "Disease Dashboard Test"


def test_api_health_requires_auth(unauthenticated_client: TestClient):
    """Test that /api/health requires authentication"""
    response = unauthenticated_client.get("/api/health")

    # Should return 401 when no auth provided and keys are configured
    assert response.status_code == 401


def test_api_health_with_valid_auth(authenticated_client: TestClient):
    """Test /api/health with valid authentication"""
    response = authenticated_client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database_initialized" in data
    assert isinstance(data["database_initialized"], bool)


def test_api_health_with_invalid_auth(unauthenticated_client: TestClient):
    """Test /api/health with invalid authentication"""
    response = unauthenticated_client.get(
        "/api/health", headers={"Authorization": "Bearer invalid-key"}
    )

    assert response.status_code == 401


def test_get_diseases_requires_auth(unauthenticated_client: TestClient):
    """Test that /api/diseases requires authentication"""
    response = unauthenticated_client.get("/api/diseases")

    assert response.status_code == 401


def test_get_diseases_with_auth(authenticated_client: TestClient):
    """Test getting list of diseases with authentication"""
    response = authenticated_client.get("/api/diseases")

    assert response.status_code == 200
    data = response.json()

    assert "diseases" in data
    assert "count" in data
    assert isinstance(data["diseases"], list)
    assert data["count"] == len(data["diseases"])

    # Check we have diseases from test data
    assert data["count"] > 0
    disease_names = [d["name"] for d in data["diseases"]]
    # measles should be in the actual test data
    assert "measles" in disease_names


def test_get_stats_requires_auth(unauthenticated_client: TestClient):
    """Test that /api/stats requires authentication"""
    response = unauthenticated_client.get("/api/stats")

    assert response.status_code == 401


def test_get_stats_with_auth(authenticated_client: TestClient):
    """Test getting summary statistics with authentication"""
    response = authenticated_client.get("/api/stats")

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "total_states" in data
    assert "total_cases" in data
    assert "earliest_date" in data
    assert "latest_date" in data

    # Verify values from initialized test data
    assert data["total_states"] > 0
    assert data["total_cases"] > 0
    assert data["earliest_date"] is not None
    assert data["latest_date"] is not None


def test_multiple_api_keys(test_settings, monkeypatch):
    """Test that multiple API keys work"""
    from app.main import app

    # Mock settings with multiple keys
    monkeypatch.setattr("app.config.settings", test_settings)
    monkeypatch.setattr("app.auth.settings", test_settings)
    monkeypatch.setattr("app.main.settings", test_settings)
    monkeypatch.setattr("app.database.settings", test_settings)

    # Test with first key
    client1 = TestClient(app)
    client1.headers = {"Authorization": "Bearer test-key-123"}
    response1 = client1.get("/api/health")
    assert response1.status_code == 200

    # Test with second key
    client2 = TestClient(app)
    client2.headers = {"Authorization": "Bearer test-key-456"}
    response2 = client2.get("/api/health")
    assert response2.status_code == 200


def test_bearer_token_format(authenticated_client: TestClient):
    """Test that Bearer token format is properly handled"""
    # Already tested via authenticated_client fixture
    response = authenticated_client.get("/api/health")
    assert response.status_code == 200


def test_missing_bearer_prefix(unauthenticated_client: TestClient):
    """Test authentication fails without Bearer prefix"""
    response = unauthenticated_client.get(
        "/api/health", headers={"Authorization": "test-key-123"}
    )

    # Should fail - needs "Bearer" prefix
    assert response.status_code == 401


def test_dev_mode_no_keys(no_auth_settings, test_data_dir, monkeypatch):
    """Test that dev mode (no API keys) allows all access"""
    from app.main import app

    # Mock settings with no API keys
    monkeypatch.setattr("app.config.settings", no_auth_settings)
    monkeypatch.setattr("app.auth.settings", no_auth_settings)
    monkeypatch.setattr("app.main.settings", no_auth_settings)
    monkeypatch.setattr("app.database.settings", no_auth_settings)

    client = TestClient(app)

    # Should work without auth when no keys configured
    response = client.get("/api/health")
    assert response.status_code == 200


def test_api_endpoints_return_json(authenticated_client: TestClient):
    """Test that API endpoints return JSON content type"""
    endpoints = ["/health", "/api/health", "/api/diseases", "/api/stats"]

    for endpoint in endpoints:
        response = authenticated_client.get(endpoint)
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
