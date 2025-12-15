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

from app.etl.normalizers.disease_names import apply_disease_aliases
from app.etl.schema import REQUIRED_COLUMNS, validate_dataframe
from app.etl.storage import get_filesystem, get_storage_options, is_remote_uri
from app.utils import to_disease_slug

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
        1. Source-specific transformation (abstract)
        2. Apply disease name aliases (shared)
        3. Generate URL slugs (shared)
        4. Tag with data source (shared)
        5. Validate schema (shared)

        Returns:
            DataFrame conforming to the unified schema
        """
        logger.info(f"Loading data from {self.get_source_name()}: {self.source_uri}")

        # Step 1: Source-specific loading and transformation
        df = self.transform()

        # Handle empty DataFrames (e.g., missing data directory)
        if df.empty:
            logger.warning(f"No data found for {self.get_source_name()}")
            return df

        logger.info(f"Transformed {len(df)} records from {self.get_source_name()}")

        # Step 2: Apply disease name aliases
        df = self._apply_disease_aliases(df)

        # Step 3: Generate URL slugs
        df = self._generate_slugs(df)

        # Step 4: Tag with data source
        df = self._tag_data_source(df)

        # Step 5: Validate schema
        self._validate_schema(df)

        # Step 6: Select and order columns
        df = self._select_columns(df)

        logger.info(f"Loaded {len(df)} records from {self.get_source_name()}")
        return df

    @abstractmethod
    def transform(self) -> pd.DataFrame:
        """
        Source-specific transformation logic.

        Must return a DataFrame with columns matching the unified schema.
        The following columns are handled by the base class and should NOT
        be set in transform():
            - disease_slug (generated from disease_name)
            - data_source (set from get_source_name())

        The following columns MUST be set:
            - report_period_start
            - report_period_end
            - date_type
            - time_unit
            - disease_name
            - original_disease_name
            - reporting_jurisdiction
            - state
            - geo_name
            - geo_unit
            - outcome
            - count

        Optional columns (can be None/NaN):
            - disease_subtype
            - age_group
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

    def _apply_disease_aliases(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply disease name aliases from centralized configuration.

        This normalizes disease names across sources by mapping variant
        names to canonical forms (e.g., "Hansen's Disease" -> "Leprosy").
        """
        return apply_disease_aliases(df)

    def _generate_slugs(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate URL-safe slugs for disease names.

        Creates the 'disease_slug' column from 'disease_name'.
        """
        df = df.copy()
        df["disease_slug"] = df["disease_name"].apply(
            lambda x: to_disease_slug(x) if pd.notna(x) else None
        )
        return df

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
