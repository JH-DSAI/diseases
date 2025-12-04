"""
Unified schema definition for disease data.

This module defines the canonical schema that all data sources must
conform to after transformation. It serves as the single source of
truth for the disease_data table structure.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd

# Column names in the unified schema (order matters for consistency)
REQUIRED_COLUMNS = [
    "report_period_start",
    "report_period_end",
    "date_type",
    "time_unit",
    "disease_name",
    "disease_slug",
    "disease_subtype",
    "reporting_jurisdiction",
    "state",
    "geo_name",
    "geo_unit",
    "age_group",
    "confirmation_status",
    "outcome",
    "count",
    "data_source",
    "original_disease_name",
]

# Expected pandas dtypes for each column
SCHEMA_DTYPES: dict[str, Any] = {
    "report_period_start": "datetime64[ns]",
    "report_period_end": "datetime64[ns]",
    "date_type": "object",  # string
    "time_unit": "object",  # string
    "disease_name": "object",  # string
    "disease_slug": "object",  # string
    "disease_subtype": "object",  # string, nullable
    "reporting_jurisdiction": "object",  # string
    "state": "object",  # string
    "geo_name": "object",  # string
    "geo_unit": "object",  # string
    "age_group": "object",  # string, nullable
    "confirmation_status": "object",  # string, nullable
    "outcome": "object",  # string
    "count": "Int64",  # nullable integer
    "data_source": "object",  # string
    "original_disease_name": "object",  # string
}

# Columns that are allowed to have null/NA values
NULLABLE_COLUMNS = {
    "disease_subtype",
    "age_group",
    "confirmation_status",
    "count",  # Some records may have missing counts
}

# Columns that must have non-null values
REQUIRED_NON_NULL = set(REQUIRED_COLUMNS) - NULLABLE_COLUMNS


def validate_dataframe(df: "pd.DataFrame") -> list[str]:
    """
    Validate a DataFrame against the unified schema.

    Args:
        df: DataFrame to validate

    Returns:
        List of validation error messages (empty if valid)
    """

    errors = []

    # Check for missing columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        errors.append(f"Missing columns: {sorted(missing_cols)}")

    # Check for extra columns (warning, not error)
    extra_cols = set(df.columns) - set(REQUIRED_COLUMNS)
    if extra_cols:
        # Log warning but don't fail
        pass

    # Check for null values in required columns
    for col in REQUIRED_NON_NULL:
        if col in df.columns and df[col].isna().any():
            null_count = df[col].isna().sum()
            errors.append(f"Column '{col}' has {null_count} null values")

    return errors
