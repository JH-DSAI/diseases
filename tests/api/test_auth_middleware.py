"""Tests for HTTP Basic Auth middleware.

These tests verify that staging authentication:
1. Is disabled by default (requests pass through)
2. When enabled, blocks unauthenticated requests with 401
3. When enabled, allows authenticated requests with valid credentials
4. When enabled, rejects invalid credentials with 401
5. Always allows /health endpoint (for health checks)
"""

import base64

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings
from app.middleware import AuthConfig, BasicAuthMiddleware, parse_basic_auth, verify_credentials

# =============================================================================
# Pure Function Tests (no app/middleware needed)
# =============================================================================


class TestParseBasicAuth:
    """Tests for the parse_basic_auth pure function."""

    def test_valid_basic_auth(self):
        """Valid Basic auth header should return username and password."""
        header = "Basic " + base64.b64encode(b"user:pass").decode()
        result = parse_basic_auth(header)
        assert result == ("user", "pass")

    def test_password_with_colons(self):
        """Password containing colons should be handled correctly."""
        header = "Basic " + base64.b64encode(b"user:pass:with:colons").decode()
        result = parse_basic_auth(header)
        assert result == ("user", "pass:with:colons")

    def test_wrong_scheme_returns_none(self):
        """Non-Basic scheme should return None."""
        result = parse_basic_auth("Bearer sometoken")
        assert result is None

    def test_malformed_base64_returns_none(self):
        """Invalid base64 should return None."""
        result = parse_basic_auth("Basic !!notbase64!!")
        assert result is None

    def test_missing_colon_returns_none(self):
        """Credentials without colon separator should return None."""
        header = "Basic " + base64.b64encode(b"userpassnocolon").decode()
        result = parse_basic_auth(header)
        assert result is None

    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        result = parse_basic_auth("")
        assert result is None

    def test_case_insensitive_scheme(self):
        """Scheme comparison should be case-insensitive."""
        header = "BASIC " + base64.b64encode(b"user:pass").decode()
        result = parse_basic_auth(header)
        assert result == ("user", "pass")


class TestVerifyCredentials:
    """Tests for the verify_credentials pure function."""

    def test_valid_credentials_return_true(self):
        """Matching credentials should return True."""
        assert verify_credentials("admin", "secret", "admin", "secret") is True

    def test_wrong_username_returns_false(self):
        """Wrong username should return False."""
        assert verify_credentials("wrong", "secret", "admin", "secret") is False

    def test_wrong_password_returns_false(self):
        """Wrong password should return False."""
        assert verify_credentials("admin", "wrong", "admin", "secret") is False

    def test_both_wrong_returns_false(self):
        """Both wrong should return False."""
        assert verify_credentials("wrong", "wrong", "admin", "secret") is False

    def test_empty_credentials_return_false(self):
        """Empty credentials don't match non-empty expected."""
        assert verify_credentials("", "", "admin", "secret") is False

    def test_unicode_credentials(self):
        """Unicode credentials should work correctly."""
        assert verify_credentials("用户", "密码", "用户", "密码") is True


# =============================================================================
# AuthConfig Tests
# =============================================================================


class TestAuthConfig:
    """Tests for AuthConfig dataclass."""

    def test_default_excluded_paths(self):
        """Default excluded paths should include /health."""
        config = AuthConfig(enabled=True, username="admin", password="secret")
        assert "/health" in config.excluded_paths

    def test_custom_excluded_paths(self):
        """Custom excluded paths should override default."""
        config = AuthConfig(
            enabled=True,
            username="admin",
            password="secret",
            excluded_paths=frozenset({"/health", "/ready"}),
        )
        assert "/health" in config.excluded_paths
        assert "/ready" in config.excluded_paths

    def test_from_settings(self, monkeypatch):
        """from_settings should load from app.config.settings."""
        test_settings = Settings(
            app_name="Test",
            database_path=":memory:",
            staging_auth_enabled=True,
            staging_auth_username="testuser",
            staging_auth_password="testpass",
        )
        monkeypatch.setattr("app.middleware.auth.settings", test_settings)

        config = AuthConfig.from_settings()
        assert config.enabled is True
        assert config.username == "testuser"
        assert config.password == "testpass"


# =============================================================================
# Middleware Integration Tests (with explicit config - no monkeypatching)
# =============================================================================


def create_test_app(config: AuthConfig) -> FastAPI:
    """Create a minimal FastAPI app with auth middleware using explicit config."""
    app = FastAPI()
    app.add_middleware(BasicAuthMiddleware, config=config)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/test")
    def test_endpoint():
        return {"message": "authenticated"}

    @app.get("/")
    def root():
        return {"message": "home"}

    return app


def make_basic_auth_header(username: str, password: str) -> dict:
    """Create HTTP Basic Auth header."""
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {credentials}"}


class TestMiddlewareAuthDisabled:
    """Tests when auth is disabled."""

    @pytest.fixture
    def client(self) -> TestClient:
        config = AuthConfig(enabled=False, username="admin", password="secret")
        return TestClient(create_test_app(config))

    def test_requests_pass_without_auth(self, client: TestClient):
        """When auth is disabled, requests should pass through."""
        response = client.get("/api/test")
        assert response.status_code == 200
        assert response.json() == {"message": "authenticated"}

    def test_root_accessible(self, client: TestClient):
        """Root endpoint accessible when auth disabled."""
        response = client.get("/")
        assert response.status_code == 200

    def test_health_accessible(self, client: TestClient):
        """Health endpoint accessible when auth disabled."""
        response = client.get("/health")
        assert response.status_code == 200


class TestMiddlewareAuthEnabled:
    """Tests when auth is enabled."""

    @pytest.fixture
    def config(self) -> AuthConfig:
        return AuthConfig(enabled=True, username="testuser", password="testpass")

    @pytest.fixture
    def client(self, config: AuthConfig) -> TestClient:
        return TestClient(create_test_app(config))

    def test_unauthenticated_request_returns_401(self, client: TestClient):
        """Requests without credentials should return 401."""
        response = client.get("/api/test")
        assert response.status_code == 401

    def test_401_includes_www_authenticate_header(self, client: TestClient):
        """401 response should include WWW-Authenticate header."""
        response = client.get("/api/test")
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        assert "Basic" in response.headers["WWW-Authenticate"]

    def test_valid_credentials_allow_access(self, client: TestClient):
        """Requests with valid credentials should succeed."""
        headers = make_basic_auth_header("testuser", "testpass")
        response = client.get("/api/test", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "authenticated"}

    def test_invalid_username_returns_401(self, client: TestClient):
        """Wrong username should return 401."""
        headers = make_basic_auth_header("wronguser", "testpass")
        response = client.get("/api/test", headers=headers)
        assert response.status_code == 401

    def test_invalid_password_returns_401(self, client: TestClient):
        """Wrong password should return 401."""
        headers = make_basic_auth_header("testuser", "wrongpass")
        response = client.get("/api/test", headers=headers)
        assert response.status_code == 401

    def test_health_bypasses_auth(self, client: TestClient):
        """Health endpoint should be accessible without auth."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_root_requires_auth(self, client: TestClient):
        """Root endpoint should require auth when enabled."""
        response = client.get("/")
        assert response.status_code == 401


class TestMiddlewareEdgeCases:
    """Edge case tests for auth middleware."""

    @pytest.fixture
    def config(self) -> AuthConfig:
        return AuthConfig(enabled=True, username="user", password="pass")

    @pytest.fixture
    def client(self, config: AuthConfig) -> TestClient:
        return TestClient(create_test_app(config))

    def test_malformed_auth_header_returns_401(self, client: TestClient):
        """Malformed Authorization header should return 401."""
        response = client.get("/api/test", headers={"Authorization": "Basic !!invalid!!"})
        assert response.status_code == 401

    def test_bearer_token_returns_401(self, client: TestClient):
        """Bearer auth scheme should return 401."""
        response = client.get("/api/test", headers={"Authorization": "Bearer token"})
        assert response.status_code == 401

    def test_empty_credentials_returns_401(self, client: TestClient):
        """Empty username/password should return 401."""
        headers = make_basic_auth_header("", "")
        response = client.get("/api/test", headers=headers)
        assert response.status_code == 401

    def test_password_with_colons_works(self):
        """Password containing colons should work correctly."""
        config = AuthConfig(enabled=True, username="user", password="pass:with:colons")
        client = TestClient(create_test_app(config))

        headers = make_basic_auth_header("user", "pass:with:colons")
        response = client.get("/api/test", headers=headers)
        assert response.status_code == 200


# =============================================================================
# Default Settings Tests
# =============================================================================


class TestDefaultSettings:
    """Tests that verify default settings behavior."""

    def test_auth_disabled_by_default(self):
        """Verify staging_auth_enabled defaults to False."""
        settings = Settings(app_name="Test", database_path=":memory:")
        assert settings.staging_auth_enabled is False

    def test_default_username_is_admin(self):
        """Verify default username is 'admin'."""
        settings = Settings(app_name="Test", database_path=":memory:")
        assert settings.staging_auth_username == "admin"

    def test_default_password_is_empty(self):
        """Verify default password is empty string."""
        settings = Settings(app_name="Test", database_path=":memory:")
        assert settings.staging_auth_password == ""
