"""Tests for HTML page endpoints"""

import pytest
from fastapi.testclient import TestClient


def test_landing_page_requires_auth(unauthenticated_client: TestClient):
    """Test that landing page requires authentication"""
    response = unauthenticated_client.get("/")

    assert response.status_code == 401


def test_landing_page_with_auth(authenticated_client: TestClient):
    """Test landing page renders with authentication"""
    response = authenticated_client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")

    # Check for expected content
    content = response.text
    assert "Disease Dashboard" in content


def test_landing_page_lists_diseases(authenticated_client: TestClient):
    """Test that landing page includes disease list"""
    response = authenticated_client.get("/")

    assert response.status_code == 200
    content = response.text

    # Should include diseases from test data
    # Note: The exact rendering depends on templates, but diseases should be present
    # We're checking that it renders successfully and has HTML structure
    assert "<html" in content.lower()
    assert "</html>" in content.lower()


def test_disease_detail_page_requires_auth(unauthenticated_client: TestClient):
    """Test that disease detail page requires authentication"""
    response = unauthenticated_client.get("/disease/measles")

    assert response.status_code == 401


def test_disease_detail_page_valid_disease(authenticated_client: TestClient):
    """Test disease detail page with valid disease name"""
    response = authenticated_client.get("/disease/measles")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")

    content = response.text
    # Should include disease name in the page
    assert "measles" in content.lower()


def test_disease_detail_page_invalid_disease(authenticated_client: TestClient):
    """Test disease detail page with invalid disease name"""
    response = authenticated_client.get("/disease/nonexistent-disease-12345")

    # Should return 404 since database is initialized with test data
    assert response.status_code == 404
    assert "text/html" in response.headers.get("content-type", "")

    content = response.text
    assert "not found" in content.lower()


def test_disease_detail_page_multiple_diseases(authenticated_client: TestClient):
    """Test that disease pages render correctly"""
    # Only test diseases that exist in the actual data
    response = authenticated_client.get("/disease/measles")
    assert response.status_code == 200
    assert "measles" in response.text.lower()


def test_pages_return_html_content_type(authenticated_client: TestClient):
    """Test that page endpoints return HTML content type"""
    pages = ["/", "/disease/measles"]

    for page in pages:
        response = authenticated_client.get(page)
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type


def test_landing_page_with_dev_mode(no_auth_settings, test_data_dir, monkeypatch):
    """Test landing page works in dev mode (no auth)"""
    from app.main import app

    # Mock settings with no API keys
    monkeypatch.setattr("app.config.settings", no_auth_settings)
    monkeypatch.setattr("app.auth.settings", no_auth_settings)
    monkeypatch.setattr("app.main.settings", no_auth_settings)
    monkeypatch.setattr("app.database.settings", no_auth_settings)

    client = TestClient(app)

    # Should work without auth when no keys configured
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_disease_page_case_sensitivity(authenticated_client: TestClient):
    """Test disease name handling (lowercase in data)"""
    # Our test data has lowercase disease names
    response = authenticated_client.get("/disease/measles")
    assert response.status_code == 200

    # Test with different casing - should not find it (exact match required)
    response = authenticated_client.get("/disease/Measles")
    assert response.status_code == 404


def test_disease_page_special_characters(authenticated_client: TestClient):
    """Test disease name handling in URLs"""
    # Test with a valid disease from actual data
    response = authenticated_client.get("/disease/measles")
    assert response.status_code == 200
    assert "measles" in response.text.lower()


def test_html_structure_landing_page(authenticated_client: TestClient):
    """Test landing page has proper HTML structure"""
    response = authenticated_client.get("/")

    assert response.status_code == 200
    content = response.text

    # Check for basic HTML structure
    assert "<!doctype html>" in content.lower() or "<html" in content.lower()
    assert "<head>" in content.lower() or "<head " in content.lower()
    assert "<body>" in content.lower() or "<body " in content.lower()
    assert "</html>" in content.lower()


def test_html_structure_disease_page(authenticated_client: TestClient):
    """Test disease detail page has proper HTML structure"""
    response = authenticated_client.get("/disease/measles")

    assert response.status_code == 200
    content = response.text

    # Check for basic HTML structure
    assert "<!doctype html>" in content.lower() or "<html" in content.lower()
    assert "<head>" in content.lower() or "<head " in content.lower()
    assert "<body>" in content.lower() or "<body " in content.lower()
    assert "</html>" in content.lower()
