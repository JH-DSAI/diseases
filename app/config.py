"""Application configuration"""

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def get_env_files() -> tuple[str, ...]:
    """Determine which env files to load based on APP_ENV.

    Loading order (later files override earlier):
    1. .env.{APP_ENV} - environment-specific settings
    2. .env - local overrides (gitignored, for secrets/customization)
    """
    app_env = os.getenv("APP_ENV", "development")
    env_file = f".env.{app_env}"
    return (env_file, ".env")


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "Disease Dashboard"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    data_directory: Path = Path(__file__).parent.parent / "us_disease_tracker_data"
    nndss_data_directory: Path = Path(__file__).parent.parent / "nndss_data"
    database_path: str = "disease_dashboard.duckdb"  # Persistent DuckDB file

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Staging auth (HTTP Basic Auth for dev/staging environments)
    staging_auth_enabled: bool = False
    staging_auth_username: str = "admin"
    staging_auth_password: str = ""

    # Azure Blob Storage (for remote data)
    azure_storage_account: str = ""
    azure_storage_key: str = ""

    # Data source URIs (az://container/path for Azure, empty for local filesystem)
    data_uri: str = ""
    nndss_data_uri: str = ""

    model_config = SettingsConfigDict(
        env_file=get_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Global settings instance
settings = Settings()
