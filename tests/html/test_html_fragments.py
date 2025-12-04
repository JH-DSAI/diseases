"""Tests for HTML fragment endpoints (HTMX)."""

from fastapi.testclient import TestClient


class TestDiseaseCardsFragment:
    """Tests for /api/html/diseases endpoint."""

    def test_returns_html(self, client: TestClient):
        """Test endpoint returns HTML content type."""
        response = client.get("/api/html/diseases")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_contains_disease_links(self, client: TestClient):
        """Test response contains links to disease pages."""
        response = client.get("/api/html/diseases")
        content = response.text
        # Should have links to disease detail pages
        assert "/disease/" in content

    def test_displays_disease_names(self, client: TestClient):
        """Test response displays disease names."""
        response = client.get("/api/html/diseases")
        content = response.text.lower()
        # Should contain at least one disease name from fixtures
        assert "measles" in content or "pertussis" in content


class TestDiseaseStatsFragment:
    """Tests for /api/html/disease/{slug}/stats endpoint."""

    def test_returns_html(self, client: TestClient):
        """Test endpoint returns HTML content type."""
        response = client.get("/api/html/disease/measles/stats")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_invalid_disease_returns_404(self, client: TestClient):
        """Test 404 for nonexistent disease."""
        response = client.get("/api/html/disease/nonexistent-xyz/stats")
        assert response.status_code == 404


class TestTimeseriesFragment:
    """Tests for /api/html/disease/{slug}/timeseries endpoint."""

    def test_returns_html(self, client: TestClient):
        """Test endpoint returns HTML content type."""
        response = client.get("/api/html/disease/measles/timeseries")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_granularity_parameter(self, client: TestClient):
        """Test granularity query parameter is accepted."""
        response = client.get("/api/html/disease/measles/timeseries?granularity=week")
        assert response.status_code == 200

    def test_invalid_disease_returns_404(self, client: TestClient):
        """Test 404 for nonexistent disease."""
        response = client.get("/api/html/disease/nonexistent-xyz/timeseries")
        assert response.status_code == 404


class TestAgeGroupFragment:
    """Tests for /api/html/disease/{slug}/age-groups endpoint."""

    def test_returns_html(self, client: TestClient):
        """Test endpoint returns HTML content type."""
        response = client.get("/api/html/disease/measles/age-groups")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_invalid_disease_returns_404(self, client: TestClient):
        """Test 404 for nonexistent disease."""
        response = client.get("/api/html/disease/nonexistent-xyz/age-groups")
        assert response.status_code == 404
