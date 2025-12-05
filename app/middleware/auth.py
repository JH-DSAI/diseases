"""HTTP Basic Authentication middleware for staging environment protection."""

import base64
import secrets
from dataclasses import dataclass

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings


@dataclass(frozen=True)
class AuthConfig:
    """Configuration for Basic Auth middleware."""

    enabled: bool
    username: str
    password: str
    excluded_paths: frozenset[str] = frozenset({"/health"})

    @classmethod
    def from_settings(cls) -> "AuthConfig":
        """Create AuthConfig from app settings."""
        return cls(
            enabled=settings.staging_auth_enabled,
            username=settings.staging_auth_username,
            password=settings.staging_auth_password,
        )


def parse_basic_auth(auth_header: str) -> tuple[str, str] | None:
    """
    Parse HTTP Basic Auth header and extract credentials.

    Args:
        auth_header: The Authorization header value (e.g., "Basic dXNlcjpwYXNz")

    Returns:
        Tuple of (username, password) if valid, None otherwise.
    """
    try:
        scheme, credentials = auth_header.split(" ", 1)
        if scheme.lower() != "basic":
            return None

        decoded = base64.b64decode(credentials).decode("utf-8")
        username, password = decoded.split(":", 1)
        return (username, password)

    except (ValueError, UnicodeDecodeError):
        return None


def verify_credentials(
    username: str,
    password: str,
    expected_username: str,
    expected_password: str,
) -> bool:
    """
    Verify credentials using timing-safe comparison.

    Args:
        username: Provided username
        password: Provided password
        expected_username: Expected username to match
        expected_password: Expected password to match

    Returns:
        True if both username and password match, False otherwise.
    """
    username_valid = secrets.compare_digest(
        username.encode("utf-8"),
        expected_username.encode("utf-8"),
    )
    password_valid = secrets.compare_digest(
        password.encode("utf-8"),
        expected_password.encode("utf-8"),
    )
    return username_valid and password_valid


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces HTTP Basic Authentication.

    When enabled, all requests (except excluded paths like /health)
    require valid credentials. The browser will display a native login dialog.

    Can be configured with explicit AuthConfig for testing, or uses
    app settings by default.
    """

    def __init__(self, app, config: AuthConfig | None = None):
        super().__init__(app)
        self._config = config

    @property
    def config(self) -> AuthConfig:
        """Get config, loading from settings if not explicitly set."""
        if self._config is not None:
            return self._config
        return AuthConfig.from_settings()

    async def dispatch(self, request: Request, call_next) -> Response:
        config = self.config

        # Skip auth if disabled
        if not config.enabled:
            return await call_next(request)

        # Skip auth for excluded paths (e.g., health checks)
        if request.url.path in config.excluded_paths:
            return await call_next(request)

        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header:
            parsed = parse_basic_auth(auth_header)
            if parsed:
                username, password = parsed
                if verify_credentials(username, password, config.username, config.password):
                    return await call_next(request)

        # Return 401 with WWW-Authenticate header to trigger browser dialog
        return Response(
            content="Unauthorized",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Staging Access"'},
        )
