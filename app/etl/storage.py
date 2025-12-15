"""
Storage abstraction for local and remote filesystem access.

Uses fsspec to provide a unified interface for reading files from:
- Local filesystem (default)
- Azure Blob Storage (az://)
- S3 (s3://) - if needed in future
"""

import logging
from urllib.parse import urlparse

import fsspec

from app.config import settings

logger = logging.getLogger(__name__)


def get_storage_options() -> dict:
    """
    Build storage_options dict from settings for Azure Blob Storage.

    Returns:
        Dictionary with Azure credentials if configured, empty dict otherwise.
    """
    if settings.azure_storage_account and settings.azure_storage_key:
        return {
            "account_name": settings.azure_storage_account,
            "account_key": settings.azure_storage_key,
        }
    return {}


def get_filesystem(uri: str | object) -> tuple[fsspec.AbstractFileSystem, str]:
    """
    Get a filesystem instance and path from a URI.

    Supports:
    - Empty string or local path: returns local filesystem
    - Path objects: converted to string, treated as local filesystem
    - az://container/path: returns Azure Blob filesystem
    - s3://bucket/path: returns S3 filesystem (if configured)

    Args:
        uri: URI string (e.g., "az://mycontainer/data" or "/local/path") or Path object

    Returns:
        Tuple of (filesystem, path) where path is the path within the filesystem
    """
    # Convert Path objects to string
    uri_str = str(uri) if uri else ""

    if not uri_str or uri_str.startswith("/") or not urlparse(uri_str).scheme:
        # Local filesystem (includes relative paths and Path objects)
        fs = fsspec.filesystem("file")
        return fs, uri_str if uri_str else "."

    parsed = urlparse(uri_str)
    scheme = parsed.scheme

    if scheme == "az" or scheme == "abfs":
        # Azure Blob Storage
        storage_options = get_storage_options()
        fs = fsspec.filesystem("az", **storage_options)
        # Path is container/path
        path = f"{parsed.netloc}{parsed.path}"
        return fs, path

    if scheme == "s3":
        # S3 - credentials would come from environment or storage_options
        fs = fsspec.filesystem("s3")
        path = f"{parsed.netloc}{parsed.path}"
        return fs, path

    # Fallback to local filesystem
    logger.warning(f"Unknown URI scheme '{scheme}', treating as local path: {uri_str}")
    fs = fsspec.filesystem("file")
    return fs, uri_str


def is_remote_uri(uri: str) -> bool:
    """Check if a URI points to remote storage."""
    if not uri:
        return False
    parsed = urlparse(uri)
    return parsed.scheme in ("az", "abfs", "s3", "gs")
