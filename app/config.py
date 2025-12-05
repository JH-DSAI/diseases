"""Application configuration"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


# Global settings instance
settings = Settings()
