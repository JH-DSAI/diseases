"""Authentication middleware and utilities"""

import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

# HTTP Bearer token security
security = HTTPBearer(auto_error=False)


def verify_api_key(credentials: HTTPAuthorizationCredentials | None = Security(security)) -> bool:
    """
    Verify API key from Authorization header.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        True if authenticated

    Raises:
        HTTPException: If authentication fails
    """
    # Get API keys from settings
    api_keys = settings.get_api_keys()

    # If no API keys configured, allow all access (dev mode)
    if not api_keys:
        return True

    # Check for credentials
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token against configured API keys
    token = credentials.credentials
    if token not in api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True


def generate_api_key() -> str:
    """
    Generate a secure random API key.

    Returns:
        A 32-character hexadecimal API key
    """
    return secrets.token_hex(32)


# Example usage in routes:
# @app.get("/protected")
# async def protected_route(authenticated: bool = Depends(verify_api_key)):
#     return {"message": "You are authenticated"}
