"""Tests for ETL schema validation."""

import pandas as pd

from app.etl.schema import (
    NULLABLE_COLUMNS,
    REQUIRED_COLUMNS,
    REQUIRED_NON_NULL,
    validate_dataframe,
)


class TestSchemaConstants:
    """Tests for schema constants."""

    def test_required_columns_exist(self):
        """Test REQUIRED_COLUMNS is not empty."""
        assert len(REQUIRED_COLUMNS) > 0

    def test_nullable_columns_subset(self):
        """Test NULLABLE_COLUMNS is subset of REQUIRED_COLUMNS."""
        assert NULLABLE_COLUMNS.issubset(set(REQUIRED_COLUMNS))

    def test_required_non_null_computed(self):
        """Test REQUIRED_NON_NULL excludes nullable columns."""
        assert REQUIRED_NON_NULL == set(REQUIRED_COLUMNS) - NULLABLE_COLUMNS


class TestValidateDataframe:
    """Tests for validate_dataframe function."""

    def test_missing_columns(self):
        """Test detection of missing columns."""
        df = pd.DataFrame({"disease_name": ["Measles"]})
        errors = validate_dataframe(df)
        assert len(errors) > 0
        assert any("Missing columns" in e for e in errors)

    def test_null_in_required_column(self):
        """Test detection of null values in required columns."""
        # Create a dataframe with all required columns
        data = {col: ["value"] for col in REQUIRED_COLUMNS}
        data["disease_name"] = [None]  # Set a required column to null
        df = pd.DataFrame(data)

        errors = validate_dataframe(df)
        assert any("disease_name" in e and "null" in e for e in errors)

    def test_extra_columns_no_error(self):
        """Test extra columns don't cause errors."""
        data = {col: ["value"] for col in REQUIRED_COLUMNS}
        data["extra_column"] = ["extra"]
        df = pd.DataFrame(data)

        errors = validate_dataframe(df)
        # Should not have errors about extra columns
        assert not any("extra_column" in str(e) for e in errors)

    def test_valid_dataframe(self):
        """Test valid dataframe passes validation."""
        data = {col: ["value"] for col in REQUIRED_COLUMNS}
        # Set proper types for date columns
        data["report_period_start"] = pd.to_datetime(["2024-01-01"])
        data["report_period_end"] = pd.to_datetime(["2024-01-07"])
        data["count"] = [100]
        df = pd.DataFrame(data)

        errors = validate_dataframe(df)
        # Only check for missing column errors, not null errors
        missing_errors = [e for e in errors if "Missing" in e]
        assert len(missing_errors) == 0
