"""Shared test fixtures for the disease dashboard tests"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.database import DiseaseDatabase


@pytest.fixture
def sample_csv_data() -> str:
    """Sample CSV data for testing"""
    return """report_period_start,report_period_end,date_type,time_unit,disease_name,disease_subtype,state,reporting_jurisdiction,geo_name,geo_unit,age_group,confirmation_status,outcome,count
2025-08-03,2025-08-09,cccd,week,measles,NA,ID,ID,ID,state,1-4 y,confirmed,cases,5
2025-08-03,2025-08-09,cccd,week,measles,NA,ID,ID,ID,state,5-11 y,confirmed,cases,3
2025-08-10,2025-08-16,cccd,week,influenza,seasonal,CA,CA,CA,state,total,confirmed,cases,150
2025-08-10,2025-08-16,cccd,week,covid-19,omicron,NY,NY,NY,state,23-44 y,confirmed,cases,250
2025-08-17,2025-08-23,cccd,week,covid-19,omicron,NY,NY,NY,state,45-64 y,confirmed,cases,180
"""


@pytest.fixture
def test_data_dir(sample_csv_data: str, tmp_path: Path) -> Path:
    """Create temporary data directory with sample CSV files"""
    data_dir = tmp_path / "us_disease_tracker_data" / "data" / "states"

    # Create multiple state directories with CSV files
    states = ["ID", "CA", "NY"]
    for state in states:
        state_dir = data_dir / state
        state_dir.mkdir(parents=True, exist_ok=True)

        # Create a CSV file for each state
        csv_file = state_dir / f"20251107-test_{state}.csv"
        csv_file.write_text(sample_csv_data)

    return tmp_path / "us_disease_tracker_data"


@pytest.fixture
def test_settings(test_data_dir: Path) -> Settings:
    """Test settings with known configuration"""
    return Settings(
        app_name="Disease Dashboard Test",
        app_version="0.1.0-test",
        api_keys="test-key-123,test-key-456",
        data_dir=str(test_data_dir),
        debug=True,
    )


@pytest.fixture
def test_db(test_data_dir: Path, monkeypatch) -> Generator[DiseaseDatabase, None, None]:
    """Test database with sample data loaded"""
    # Use in-memory database for tests
    db = DiseaseDatabase()

    # Patch the settings to use test data directory
    monkeypatch.setenv("DATA_DIR", str(test_data_dir))

    try:
        db.connect()
        db.load_csv_files()
        yield db
    finally:
        db.close()


@pytest.fixture
def unauthenticated_client(test_settings, test_db, monkeypatch) -> TestClient:
    """Test client without authentication"""
    # Import here to avoid circular imports and to ensure fresh app
    from app.main import app

    # Mock settings
    monkeypatch.setattr("app.config.settings", test_settings)
    monkeypatch.setattr("app.auth.settings", test_settings)
    monkeypatch.setattr("app.main.settings", test_settings)
    monkeypatch.setattr("app.database.settings", test_settings)

    # Replace the global db instance with our test_db
    monkeypatch.setattr("app.database.db", test_db)
    monkeypatch.setattr("app.main.db", test_db)
    monkeypatch.setattr("app.routers.api.db", test_db)
    monkeypatch.setattr("app.routers.pages.db", test_db)

    # Use raise_server_exceptions=False to get proper status codes
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def authenticated_client(test_settings, test_db, monkeypatch) -> TestClient:
    """Test client with valid authentication"""
    from app.main import app

    # Mock settings
    monkeypatch.setattr("app.config.settings", test_settings)
    monkeypatch.setattr("app.auth.settings", test_settings)
    monkeypatch.setattr("app.main.settings", test_settings)
    monkeypatch.setattr("app.database.settings", test_settings)

    # Replace the global db instance with our test_db
    monkeypatch.setattr("app.database.db", test_db)
    monkeypatch.setattr("app.main.db", test_db)
    monkeypatch.setattr("app.routers.api.db", test_db)
    monkeypatch.setattr("app.routers.pages.db", test_db)

    # Use raise_server_exceptions=False to get proper status codes
    client = TestClient(app, raise_server_exceptions=False)
    # Add Authorization header with valid test key
    client.headers = {"Authorization": "Bearer test-key-123"}
    return client


@pytest.fixture
def no_auth_settings(test_data_dir: Path) -> Settings:
    """Settings with no API keys (dev mode - allow all access)"""
    return Settings(
        app_name="Disease Dashboard Test",
        app_version="0.1.0-test",
        api_keys="",  # Empty = dev mode
        data_dir=str(test_data_dir),
        debug=True,
    )
