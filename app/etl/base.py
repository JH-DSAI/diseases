"""
Base transformer class for data sources.

This module implements the Strategy pattern with Template Method for
ETL operations. Concrete transformers inherit from DataSourceTransformer
and implement the transform() method for source-specific logic.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path

import fsspec
import pandas as pd

from app.etl.schema import REQUIRED_COLUMNS, validate_dataframe
from app.etl.storage import get_filesystem, get_storage_options, is_remote_uri

logger = logging.getLogger(__name__)


class DataSourceTransformer(ABC):
    """
    Abstract base class for data source transformers.

    Implements the Template Method pattern where load() orchestrates
    the ETL pipeline and transform() is overridden by concrete classes.

    Supports both local filesystem and remote storage (Azure Blob, S3)
    via fsspec.

    Subclasses must implement:
        - transform(): Source-specific transformation logic
        - get_source_name(): Return the data source identifier
    """

    def __init__(self, source_uri: str | Path):
        """
        Initialize the transformer.

        Args:
            source_uri: URI to the data source. Can be:
                - Local path (e.g., "/path/to/data" or "data/") or Path object
                - Azure Blob URI (e.g., "az://container/path")
                - S3 URI (e.g., "s3://bucket/path")
        """
        # Convert Path objects to string for consistent handling
        self.source_uri = str(source_uri) if source_uri else ""
        self._fs: fsspec.AbstractFileSystem | None = None
        self._base_path: str | None = None

    @property
    def fs(self) -> fsspec.AbstractFileSystem:
        """Get the filesystem instance (lazily initialized)."""
        if self._fs is None:
            self._fs, self._base_path = get_filesystem(self.source_uri)
        return self._fs

    @property
    def base_path(self) -> str:
        """Get the base path within the filesystem."""
        if self._base_path is None:
            self._fs, self._base_path = get_filesystem(self.source_uri)
        return self._base_path

    @property
    def storage_options(self) -> dict:
        """Get storage options for pandas read operations."""
        if is_remote_uri(self.source_uri):
            return get_storage_options()
        return {}

    # Legacy property for backward compatibility
    @property
    def source_path(self) -> Path:
        """Legacy property for backward compatibility with local paths."""
        if is_remote_uri(self.source_uri):
            raise ValueError(
                f"source_path not available for remote URI: {self.source_uri}. "
                "Use fs and base_path instead."
            )
        return Path(self.source_uri) if self.source_uri else Path(".")

    def load(self) -> pd.DataFrame:
        """
        Template method: orchestrates the full ETL pipeline.

        This method defines the skeleton of the ETL algorithm:
        1. Source-specific transformation (abstract) - includes slugification
        2. Tag with data source (shared)
        3. Validate schema (shared)

        Returns:
            DataFrame conforming to the unified schema
        """
        logger.info(f"Loading data from {self.get_source_name()}: {self.source_uri}")

        # Step 1: Source-specific loading and transformation (includes slugification)
        df = self.transform()

        # Handle empty DataFrames (e.g., missing data directory)
        if df.empty:
            logger.warning(f"No data found for {self.get_source_name()}")
            return df

        logger.info(f"Transformed {len(df)} records from {self.get_source_name()}")

        # Step 2: Tag with data source
        df = self._tag_data_source(df)

        # Step 3: Validate schema
        self._validate_schema(df)

        # Step 4: Select and order columns
        df = self._select_columns(df)

        logger.info(f"Loaded {len(df)} records from {self.get_source_name()}")
        return df

    @abstractmethod
    def transform(self) -> pd.DataFrame:
        """
        Source-specific transformation logic.

        Must return a DataFrame with columns matching the unified schema.
        Transformers are responsible for generating all slug columns.

        The following column is handled by the base class:
            - data_source (set from get_source_name())

        Required columns (must be set by transform()):
            - report_period_start, report_period_end
            - date_type, time_unit
            - disease_name, disease_slug
            - disease_subtype, disease_subtype_slug
            - reporting_jurisdiction, reporting_jurisdiction_slug
            - state, state_slug
            - geo_name, geo_name_slug
            - geo_unit, geo_unit_slug
            - age_group, age_group_slug
            - outcome, count
            - original_disease_name

        Nullable columns (can be None/NaN):
            - disease_subtype, disease_subtype_slug
            - age_group, age_group_slug
            - confirmation_status
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """
        Return the data source identifier.

        This value is stored in the 'data_source' column and used
        to distinguish records from different sources.

        Returns:
            Source name (e.g., 'tracker', 'nndss')
        """
        pass

    def _tag_data_source(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add data_source column identifying the source.
        """
        df = df.copy()
        df["data_source"] = self.get_source_name()
        return df

    def _validate_schema(self, df: pd.DataFrame) -> None:
        """
        Validate DataFrame conforms to unified schema.

        Raises:
            ValueError: If validation fails with critical errors
        """
        errors = validate_dataframe(df)
        if errors:
            error_msg = f"Schema validation failed for {self.get_source_name()}:\n"
            error_msg += "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _select_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Select and order columns according to schema.

        Only includes columns that exist in both the DataFrame and schema.
        """
        available_columns = [col for col in REQUIRED_COLUMNS if col in df.columns]
        return df[available_columns]
