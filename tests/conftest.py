"""Shared test fixtures for the disease dashboard tests.

Performance Optimization: Session-Scoped Database
=================================================

The database fixtures use session scope, meaning the database is loaded ONCE
per test run rather than per-test. This dramatically speeds up the test suite.

IMPORTANT RAMIFICATIONS:
------------------------
1. Tests using `etl_test_db` or `client` share the same database instance.
   Tests must NOT modify the database state (INSERT/UPDATE/DELETE).

2. These fixtures are READ-ONLY. If you need to test mutations, use the
   function-scoped `test_db` fixture instead (which creates a fresh DB per test).

3. The session-scoped DB is loaded from real CSV fixtures in tests/fixtures/.
   The function-scoped `test_db` uses temporary directories with sample data.

Fixture Selection Guide:
------------------------
- `client` / `etl_test_db`: Fast, read-only API/query tests (recommended)
- `isolated_client` / `test_db`: Slower, for tests that need isolated DB state
"""

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.database import DiseaseDatabase

# =============================================================================
# Session-Scoped Paths (computed once)
# =============================================================================

FIXTURES_DIR = Path(__file__).parent / "fixtures"
TRACKER_FIXTURES_DIR = FIXTURES_DIR / "data" / "states"
NNDSS_FIXTURES_DIR = FIXTURES_DIR / "nndss"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def tracker_fixtures_dir() -> Path:
    """Path to tracker CSV fixtures (data/states structure)."""
    return TRACKER_FIXTURES_DIR


@pytest.fixture(scope="session")
def nndss_fixtures_dir() -> Path:
    """Path to NNDSS CSV fixtures."""
    return NNDSS_FIXTURES_DIR


# =============================================================================
# Session-Scoped ETL Database (loaded once per test run)
# =============================================================================


@pytest.fixture(scope="session")
def etl_test_settings() -> Settings:
    """Settings configured for ETL fixture paths."""
    return Settings(
        app_name="Disease Dashboard ETL Test",
        app_version="0.1.0-test",
        data_directory=FIXTURES_DIR,
        nndss_data_directory=NNDSS_FIXTURES_DIR,
        debug=True,
        database_path=":memory:",
    )


@pytest.fixture(scope="session")
def etl_test_db(etl_test_settings: Settings) -> Generator[DiseaseDatabase, None, None]:
    """
    Session-scoped database loaded via ETL transformers.

    Loaded ONCE per test session for maximum performance.
    """
    # Temporarily patch settings for loading
    import app.config
    import app.database

    original_config_settings = app.config.settings
    original_db_settings = app.database.settings

    app.config.settings = etl_test_settings
    app.database.settings = etl_test_settings

    db = DiseaseDatabase()
    try:
        db.connect()
        db.load_all_sources()
        yield db
    finally:
        db.close()
        # Restore original settings
        app.config.settings = original_config_settings
        app.database.settings = original_db_settings


# =============================================================================
# Test Clients
# =============================================================================


@pytest.fixture
def client(etl_test_settings: Settings, etl_test_db: DiseaseDatabase, monkeypatch) -> TestClient:
    """
    Primary test client with ETL-loaded database.

    Uses session-scoped database for fast tests. READ-ONLY.
    """
    from app.main import app

    # Mock settings and database
    monkeypatch.setattr("app.config.settings", etl_test_settings)
    monkeypatch.setattr("app.main.settings", etl_test_settings)
    monkeypatch.setattr("app.database.settings", etl_test_settings)

    # Replace the global db instance with our etl_test_db
    monkeypatch.setattr("app.database.db", etl_test_db)
    monkeypatch.setattr("app.main.db", etl_test_db)
    monkeypatch.setattr("app.routers.api.db", etl_test_db)
    monkeypatch.setattr("app.routers.pages.db", etl_test_db)
    monkeypatch.setattr("app.routers.html_api.db", etl_test_db)
    monkeypatch.setattr("app.dependencies.db", etl_test_db)

    return TestClient(app, raise_server_exceptions=False)


# =============================================================================
# Legacy/Isolated Fixtures (for tests needing fresh DB per test)
# =============================================================================


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

    states = ["ID", "CA", "NY"]
    for state in states:
        state_dir = data_dir / state
        state_dir.mkdir(parents=True, exist_ok=True)
        csv_file = state_dir / f"20251107-test_{state}.csv"
        csv_file.write_text(sample_csv_data)

    return tmp_path / "us_disease_tracker_data"


@pytest.fixture
def test_settings(test_data_dir: Path) -> Settings:
    """Test settings with known configuration"""
    return Settings(
        app_name="Disease Dashboard Test",
        app_version="0.1.0-test",
        data_directory=test_data_dir,
        database_path=":memory:",
        debug=True,
    )


@pytest.fixture
def test_db(test_settings: Settings, monkeypatch) -> Generator[DiseaseDatabase, None, None]:
    """Test database with sample data loaded via ETL pipeline."""
    monkeypatch.setattr("app.config.settings", test_settings)
    monkeypatch.setattr("app.database.settings", test_settings)

    db = DiseaseDatabase()
    try:
        db.connect()
        db.load_all_sources()
        yield db
    finally:
        db.close()


@pytest.fixture
def isolated_client(test_settings, test_db, monkeypatch) -> TestClient:
    """
    Test client with isolated (function-scoped) database.

    Use this for tests that need to modify database state.
    """
    from app.main import app

    monkeypatch.setattr("app.config.settings", test_settings)
    monkeypatch.setattr("app.main.settings", test_settings)
    monkeypatch.setattr("app.database.settings", test_settings)
    monkeypatch.setattr("app.database.db", test_db)
    monkeypatch.setattr("app.main.db", test_db)
    monkeypatch.setattr("app.routers.api.db", test_db)
    monkeypatch.setattr("app.routers.pages.db", test_db)
    monkeypatch.setattr("app.dependencies.db", test_db)

    return TestClient(app, raise_server_exceptions=False)
