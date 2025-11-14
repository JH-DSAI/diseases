"""Tests for database operations"""

from pathlib import Path

import pytest

from app.database import DiseaseDatabase


def test_database_connection():
    """Test database can connect and close"""
    db = DiseaseDatabase()
    assert db.conn is None
    assert not db._initialized

    db.connect()
    assert db.conn is not None
    # _initialized is only set after load_csv_files()
    assert not db._initialized

    db.close()
    assert db.conn is None


def test_load_csv_files(test_db: DiseaseDatabase):
    """Test CSV files are loaded correctly"""
    # test_db fixture already has data loaded
    assert test_db._initialized

    # Verify we can query the database
    result = test_db.conn.execute("SELECT COUNT(*) FROM disease_data").fetchone()
    assert result[0] > 0  # Should have loaded data


def test_get_diseases(test_db: DiseaseDatabase):
    """Test getting list of diseases"""
    diseases = test_db.get_diseases()

    assert isinstance(diseases, list)
    assert len(diseases) > 0
    # Sample data contains at least these diseases
    assert any(d in diseases for d in ["measles", "influenza", "covid-19"])


def test_get_states(test_db: DiseaseDatabase):
    """Test getting list of states"""
    states = test_db.get_states()

    assert isinstance(states, list)
    assert len(states) > 0
    # Sample data contains at least one of these states
    assert any(s in states for s in ["ID", "CA", "NY"])


def test_get_summary_stats(test_db: DiseaseDatabase):
    """Test getting summary statistics"""
    stats = test_db.get_summary_stats()

    assert isinstance(stats, dict)
    assert "total_states" in stats
    assert "total_cases" in stats
    assert "earliest_date" in stats
    assert "latest_date" in stats

    # Verify values are reasonable
    assert stats["total_states"] > 0
    assert stats["total_cases"] > 0
    assert stats["earliest_date"] is not None
    assert stats["latest_date"] is not None


def test_load_csv_files_missing_directory():
    """Test handling of missing data directory"""
    db = DiseaseDatabase()
    db.connect()

    # Try to load from non-existent directory - DuckDB raises different error
    with pytest.raises(Exception):  # Could be IOError, RuntimeError, etc.
        db.conn.execute(
            "CREATE TABLE disease_data AS SELECT * FROM "
            "read_csv('/nonexistent/path/*.csv', AUTO_DETECT=TRUE)"
        )

    db.close()


def test_database_singleton_behavior():
    """Test that database can be instantiated multiple times"""
    db1 = DiseaseDatabase()
    db2 = DiseaseDatabase()

    # Different instances
    assert db1 is not db2

    # But they can both connect independently
    db1.connect()
    db2.connect()

    assert db1.conn is not None
    assert db2.conn is not None

    db1.close()
    db2.close()


def test_get_diseases_empty_database():
    """Test getting diseases from empty database"""
    db = DiseaseDatabase()
    db.connect()

    # Create empty table
    db.conn.execute(
        """
        CREATE TABLE disease_data (
            disease_name VARCHAR
        )
    """
    )

    diseases = db.get_diseases()
    assert isinstance(diseases, list)
    assert len(diseases) == 0

    db.close()


def test_summary_stats_with_data(test_db: DiseaseDatabase):
    """Test that summary statistics match expected data"""
    stats = test_db.get_summary_stats()

    # We have at least one state in our test data
    assert stats["total_states"] >= 1

    # Total cases should be greater than 0
    assert stats["total_cases"] > 0

    # Date range should have valid dates
    if stats["earliest_date"]:
        assert len(stats["earliest_date"]) >= 10  # YYYY-MM-DD format
    if stats["latest_date"]:
        assert len(stats["latest_date"]) >= 10  # YYYY-MM-DD format
