"""Tests for time series API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestNationalTimeseriesEndpoint:
    """Tests for /api/data/timeseries/national/{slug} endpoint."""

    def test_timeseries_valid_disease(self, client: TestClient):
        """Test timeseries for a valid disease."""
        response = client.get("/api/data/timeseries/national/measles")
        assert response.status_code == 200

    def test_timeseries_returns_json(self, client: TestClient):
        """Test endpoint returns JSON."""
        response = client.get("/api/data/timeseries/national/measles")
        assert "application/json" in response.headers.get("content-type", "")

    def test_timeseries_default_granularity(self, client: TestClient):
        """Test default granularity is 'month'."""
        response = client.get("/api/data/timeseries/national/measles")
        data = response.json()
        assert data.get("granularity") == "month"

    def test_timeseries_week_granularity(self, client: TestClient):
        """Test week granularity parameter."""
        response = client.get("/api/data/timeseries/national/measles?granularity=week")
        assert response.status_code == 200
        data = response.json()
        assert data.get("granularity") == "week"

    def test_timeseries_response_structure(self, client: TestClient):
        """Test response has expected structure."""
        response = client.get("/api/data/timeseries/national/measles")
        data = response.json()

        assert "disease_name" in data
        assert "disease_slug" in data
        assert "granularity" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_timeseries_data_point_structure(self, client: TestClient):
        """Test data points have expected structure."""
        response = client.get("/api/data/timeseries/national/measles")
        data = response.json()

        if data["data"]:
            point = data["data"][0]
            assert "period" in point
            assert "total_cases" in point

    def test_timeseries_invalid_disease_returns_404(self, client: TestClient):
        """Test 404 for nonexistent disease."""
        response = client.get("/api/data/timeseries/national/nonexistent-disease")
        assert response.status_code == 404


class TestStateTimeseriesEndpoint:
    """Tests for /api/data/timeseries/states/{slug} endpoint."""

    def test_state_timeseries_valid_disease(self, client: TestClient):
        """Test state timeseries for a valid disease."""
        response = client.get("/api/data/timeseries/states/measles")
        assert response.status_code == 200

    def test_state_timeseries_response_structure(self, client: TestClient):
        """Test response has states dictionary."""
        response = client.get("/api/data/timeseries/states/measles")
        data = response.json()

        assert "states" in data
        assert "national" in data
        assert isinstance(data["states"], dict)
        assert isinstance(data["national"], list)

    def test_state_timeseries_has_available_states(self, client: TestClient):
        """Test response lists available states."""
        response = client.get("/api/data/timeseries/states/measles")
        data = response.json()

        assert "available_states" in data
        assert isinstance(data["available_states"], list)

    def test_state_timeseries_week_granularity(self, client: TestClient):
        """Test week granularity for state timeseries."""
        response = client.get("/api/data/timeseries/states/measles?granularity=week")
        assert response.status_code == 200
        data = response.json()
        assert data.get("granularity") == "week"

    def test_state_timeseries_invalid_disease_returns_404(self, client: TestClient):
        """Test 404 for nonexistent disease."""
        response = client.get("/api/data/timeseries/states/nonexistent-disease")
        assert response.status_code == 404


class TestTimeseriesQueryParameters:
    """Tests for time series query parameters."""

    @pytest.mark.parametrize("granularity", ["month", "week"])
    def test_valid_granularities(self, client: TestClient, granularity: str):
        """Test valid granularity values."""
        response = client.get(f"/api/data/timeseries/national/measles?granularity={granularity}")
        assert response.status_code == 200
        data = response.json()
        assert data["granularity"] == granularity
