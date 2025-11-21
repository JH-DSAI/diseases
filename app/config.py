"""Application configuration"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "Disease Dashboard"
    app_version: str = "0.1.0"
    debug: bool = False

    # Authentication
    secret_key: str = "change-me-in-production"
    api_keys: str = ""  # Comma-separated list in .env

    # Database
    data_directory: Path = Path(__file__).parent.parent / "us_disease_tracker_data"
    nndss_data_directory: Path = Path(__file__).parent.parent / "nndss_data"
    database_path: str = "disease_dashboard.duckdb"  # Persistent DuckDB file

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_api_keys(self) -> list[str]:
        """Parse API keys from comma-separated string"""
        if not self.api_keys:
            return []
        return [key.strip() for key in self.api_keys.split(',') if key.strip()]


# Global settings instance
settings = Settings()
