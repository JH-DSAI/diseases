"""
ETL (Extract, Transform, Load) package for disease data sources.

This package provides a Strategy pattern-based architecture for loading
and transforming data from various sources into a unified schema.

Usage:
    from app.etl.config import get_transformer, list_sources

    # Load from a specific source
    transformer = get_transformer('nndss')(source_path)
    df = transformer.load()

    # List all available sources
    sources = list_sources()  # ['tracker', 'nndss']
"""

from app.etl.base import DataSourceTransformer
from app.etl.schema import REQUIRED_COLUMNS, SCHEMA_DTYPES

__all__ = [
    "DataSourceTransformer",
    "REQUIRED_COLUMNS",
    "SCHEMA_DTYPES",
]
