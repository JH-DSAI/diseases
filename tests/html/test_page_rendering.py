"""Tests for HTML page rendering."""

from fastapi.testclient import TestClient


class TestLandingPage:
    """Tests for the landing page (/)."""

    def test_returns_html(self, client: TestClient):
        """Test landing page returns HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_has_html_structure(self, client: TestClient):
        """Test response has proper HTML document structure."""
        response = client.get("/")
        content = response.text.lower()
        assert "<!doctype html>" in content or "<html" in content
        assert "</html>" in content

    def test_has_htmx_trigger(self, client: TestClient):
        """Test landing page has HTMX trigger for loading content."""
        response = client.get("/")
        content = response.text
        # Should have HTMX attributes for dynamic loading
        assert "hx-get" in content or "hx-trigger" in content

    def test_has_page_title(self, client: TestClient):
        """Test landing page has title."""
        response = client.get("/")
        content = response.text
        assert "<title>" in content
        assert "Dashboard" in content

    def test_loads_htmx_library(self, client: TestClient):
        """Test page includes HTMX library."""
        response = client.get("/")
        content = response.text.lower()
        # Should reference htmx somewhere (in head or body)
        assert "htmx" in content


class TestDiseaseDetailPage:
    """Tests for disease detail page (/disease/{slug})."""

    def test_returns_html(self, client: TestClient):
        """Test disease page returns HTML."""
        response = client.get("/disease/measles")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_contains_disease_name(self, client: TestClient):
        """Test page contains disease name."""
        response = client.get("/disease/measles")
        content = response.text.lower()
        assert "measles" in content

    def test_has_htmx_triggers(self, client: TestClient):
        """Test disease page has HTMX triggers for loading data."""
        response = client.get("/disease/measles")
        content = response.text
        # Should have hx-get for loading stats and charts
        assert "hx-get" in content

    def test_invalid_disease_returns_404(self, client: TestClient):
        """Test 404 for nonexistent disease."""
        response = client.get("/disease/nonexistent-disease-xyz")
        assert response.status_code == 404

    def test_404_has_error_message(self, client: TestClient):
        """Test 404 page has error message."""
        response = client.get("/disease/nonexistent-disease-xyz")
        content = response.text.lower()
        assert "not found" in content

    def test_has_back_navigation(self, client: TestClient):
        """Test disease page has navigation back to landing."""
        response = client.get("/disease/measles")
        content = response.text
        # Should have a link back to home
        assert 'href="/"' in content or "href='/''" in content


class TestHTMLResponseHeaders:
    """Tests for HTML response headers."""

    def test_content_type_is_html(self, client: TestClient):
        """Test content type is text/html for pages."""
        response = client.get("/")
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type

    def test_charset_is_utf8(self, client: TestClient):
        """Test charset is utf-8."""
        response = client.get("/")
        content_type = response.headers.get("content-type", "")
        assert "utf-8" in content_type.lower()
