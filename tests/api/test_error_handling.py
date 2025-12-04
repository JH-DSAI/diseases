"""Tests for API error handling."""

import pytest
from fastapi.testclient import TestClient


class TestNotFoundErrors:
    """Tests for 404 not found errors."""

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/data/disease/nonexistent-disease-xyz/stats",
            "/api/data/disease/nonexistent-disease-xyz/age-groups",
            "/api/data/timeseries/national/nonexistent-disease-xyz",
            "/api/data/timeseries/states/nonexistent-disease-xyz",
        ],
    )
    def test_404_invalid_disease_slug(self, client: TestClient, endpoint: str):
        """Test 404 for invalid disease slug."""
        response = client.get(endpoint)
        assert response.status_code == 404

    def test_404_response_has_detail(self, client: TestClient):
        """Test 404 response contains detail message."""
        response = client.get("/api/data/disease/fake-disease/stats")
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_404_mentions_disease(self, client: TestClient):
        """Test 404 detail mentions the disease slug."""
        slug = "some-fake-disease"
        response = client.get(f"/api/data/disease/{slug}/stats")
        data = response.json()
        assert slug in data["detail"]


class TestContentTypeErrors:
    """Tests for content type validation."""

    def test_json_endpoints_return_json(self, client: TestClient):
        """Test JSON endpoints return application/json."""
        endpoints = [
            "/health",
            "/api/data/health",
            "/api/data/diseases",
            "/api/data/stats",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            assert "application/json" in response.headers.get("content-type", "")
