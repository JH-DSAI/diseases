"""Tests for disease-related API endpoints."""

from fastapi.testclient import TestClient


class TestDiseaseListEndpoint:
    """Tests for /api/data/diseases endpoint."""

    def test_diseases_returns_200(self, client: TestClient):
        """Test endpoint returns 200."""
        response = client.get("/api/data/diseases")
        assert response.status_code == 200

    def test_diseases_returns_json(self, client: TestClient):
        """Test endpoint returns JSON content type."""
        response = client.get("/api/data/diseases")
        assert "application/json" in response.headers.get("content-type", "")

    def test_diseases_response_structure(self, client: TestClient):
        """Test response has diseases and count fields."""
        response = client.get("/api/data/diseases")
        data = response.json()

        assert "diseases" in data
        assert "count" in data
        assert isinstance(data["diseases"], list)
        assert data["count"] == len(data["diseases"])

    def test_disease_item_structure(self, client: TestClient):
        """Test each disease has name and slug."""
        response = client.get("/api/data/diseases")
        data = response.json()

        if data["diseases"]:
            disease = data["diseases"][0]
            assert "name" in disease
            assert "slug" in disease

    def test_diseases_list_not_empty(self, client: TestClient):
        """Test diseases list is not empty with test data."""
        response = client.get("/api/data/diseases")
        data = response.json()
        assert data["count"] > 0


class TestDiseaseStatsEndpoint:
    """Tests for /api/data/disease/{slug}/stats endpoint."""

    def test_stats_valid_disease(self, client: TestClient):
        """Test stats for a valid disease slug."""
        response = client.get("/api/data/disease/measles/stats")
        assert response.status_code == 200

    def test_stats_response_structure(self, client: TestClient):
        """Test stats response has expected fields."""
        response = client.get("/api/data/disease/measles/stats")

        if response.status_code == 200:
            data = response.json()
            assert "total_cases" in data
            assert "affected_states" in data

    def test_stats_invalid_disease_returns_404(self, client: TestClient):
        """Test 404 for nonexistent disease."""
        response = client.get("/api/data/disease/nonexistent-xyz/stats")
        assert response.status_code == 404

    def test_stats_404_has_detail(self, client: TestClient):
        """Test 404 response has detail message."""
        response = client.get("/api/data/disease/nonexistent-xyz/stats")
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestAgeGroupEndpoint:
    """Tests for /api/data/disease/{slug}/age-groups endpoint."""

    def test_age_groups_valid_disease(self, client: TestClient):
        """Test age groups for a valid disease."""
        response = client.get("/api/data/disease/measles/age-groups")
        assert response.status_code == 200

    def test_age_groups_response_structure(self, client: TestClient):
        """Test age groups response has expected fields."""
        response = client.get("/api/data/disease/measles/age-groups")

        if response.status_code == 200:
            data = response.json()
            assert "age_groups" in data
            assert "states" in data
            assert isinstance(data["states"], dict)

    def test_age_groups_invalid_disease_returns_404(self, client: TestClient):
        """Test 404 for nonexistent disease."""
        response = client.get("/api/data/disease/fake-disease-xyz/age-groups")
        assert response.status_code == 404


class TestSummaryStatsEndpoint:
    """Tests for /api/data/stats endpoint."""

    def test_stats_returns_200(self, client: TestClient):
        """Test endpoint returns 200."""
        response = client.get("/api/data/stats")
        assert response.status_code == 200

    def test_stats_response_structure(self, client: TestClient):
        """Test response has expected fields."""
        response = client.get("/api/data/stats")
        data = response.json()

        assert "total_states" in data
        assert "total_cases" in data
        assert "earliest_date" in data
        assert "latest_date" in data

    def test_stats_values_reasonable(self, client: TestClient):
        """Test stats values are reasonable."""
        response = client.get("/api/data/stats")
        data = response.json()

        assert data["total_states"] > 0
        assert data["total_cases"] > 0
        assert data["earliest_date"] is not None
        assert data["latest_date"] is not None
