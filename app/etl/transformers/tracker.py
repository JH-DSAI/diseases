"""
State disease tracker data transformer.

This module handles loading and transforming state-submitted disease
tracker CSV data into the unified disease_data schema.

Supports both local filesystem and remote storage (Azure Blob, S3) via fsspec.
"""

import logging
from collections import defaultdict

import pandas as pd

from app.etl.base import DataSourceTransformer
from app.etl.normalizers.slugify import slugify
from app.etl.storage import is_remote_uri

logger = logging.getLogger(__name__)

# Normalize tracker subtype values to canonical form
# See docs/data-decisions.md for rationale
SUBTYPE_NORMALIZATION = {
    "other": "unspecified",
    "na": "unspecified",
    "not specified": "unspecified",
    "n/a": "unspecified",
}


class TrackerTransformer(DataSourceTransformer):
    """
    Transformer for state disease tracker CSV data.

    Handles tracker-specific transformations:
    - Selecting latest file per state
    - Date parsing from CSV columns
    - Column name normalization
    - Disease name mapping to NNDSS standard
    """

    def get_source_name(self) -> str:
        return "tracker"

    def transform(self) -> pd.DataFrame:
        """
        Load and transform tracker data to unified schema.

        Loads the latest CSV file per state from the source directory
        and combines them into a single DataFrame.

        Supports both local filesystem and remote storage via fsspec.

        Returns:
            DataFrame with tracker data in unified schema format
        """
        data_path = f"{self.base_path}/data/states"

        # Check if directory exists
        if not self.fs.exists(data_path):
            logger.warning(f"Tracker data directory not found: {data_path}")
            return pd.DataFrame()

        # Find all CSV files using fsspec glob
        all_csv_files = self.fs.glob(f"{data_path}/**/*.csv")
        logger.info(f"Found {len(all_csv_files)} total tracker CSV files")

        if not all_csv_files:
            logger.warning("No tracker CSV files found")
            return pd.DataFrame()

        # Select latest file per state
        csv_files = self._select_latest_per_state(all_csv_files)
        logger.info(f"Selected {len(csv_files)} latest files (one per state)")

        # Load and combine all files
        all_data = []
        for csv_file in csv_files:
            try:
                # Build the full URI for pandas to read
                if is_remote_uri(self.source_uri):
                    # For remote, use the protocol prefix
                    file_uri = f"az://{csv_file}"
                    df = pd.read_csv(
                        file_uri,
                        parse_dates=["report_period_start", "report_period_end"],
                        storage_options=self.storage_options,
                    )
                else:
                    # For local, use path directly
                    df = pd.read_csv(
                        csv_file,
                        parse_dates=["report_period_start", "report_period_end"],
                    )
                file_name = csv_file.split("/")[-1]
                logger.info(f"Loaded {file_name}: {len(df)} rows")
                all_data.append(df)
            except Exception as e:
                logger.error(f"Error loading {csv_file}: {e}")

        if not all_data:
            logger.error("No data loaded from tracker CSV files")
            return pd.DataFrame()

        # Combine all DataFrames
        combined_df = pd.concat(all_data, ignore_index=True)

        # Apply transformations
        combined_df = self._normalize_columns(combined_df)
        combined_df = self._normalize_disease_names(combined_df)
        combined_df = self._map_to_unified_schema(combined_df)

        logger.info(f"Transformed {len(combined_df)} total tracker records")
        return combined_df

    def _select_latest_per_state(self, csv_files: list[str]) -> list[str]:
        """
        Select the latest CSV file for each state.

        File format: YYYYMMDD-HHMMSS_STATE_UPLOADERNAME.csv

        Args:
            csv_files: List of file paths (strings from fsspec glob)

        Returns:
            List of latest file paths per state
        """
        files_by_state = defaultdict(list)

        for csv_file in csv_files:
            # Extract state from parent directory name (second to last path component)
            parts = csv_file.replace("\\", "/").split("/")
            if len(parts) >= 2:
                state = parts[-2]  # Parent directory is the state
                files_by_state[state].append(csv_file)

        # Select the latest file for each state (sorted by filename timestamp)
        latest_files = []
        for state, state_files in files_by_state.items():
            # Sort by filename (last path component)
            latest_file = sorted(state_files, key=lambda f: f.split("/")[-1], reverse=True)[0]
            latest_files.append(latest_file)
            logger.debug(f"Selected latest file for {state}: {latest_file.split('/')[-1]}")

        return latest_files

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names for consistency."""
        df = df.copy()

        # Handle both 'reporting_jurisdiction' and 'state' columns
        if "reporting_jurisdiction" in df.columns and "state" not in df.columns:
            df["state"] = df["reporting_jurisdiction"]
        elif "state" in df.columns and "reporting_jurisdiction" not in df.columns:
            df["reporting_jurisdiction"] = df["state"]

        return df

    def _normalize_disease_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Store original disease name for provenance."""
        df = df.copy()
        df["original_disease_name"] = df["disease_name"]
        return df

    def _map_to_unified_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map tracker fields to the unified disease_data schema.

        Tracker names are the canonical source for disease names.
        All dimension columns get corresponding _slug columns for matching.
        """
        unified = pd.DataFrame()

        # Date/time fields
        unified["report_period_start"] = df["report_period_start"]
        unified["report_period_end"] = df["report_period_end"]
        unified["date_type"] = df.get("date_type", "cccd")
        unified["time_unit"] = df.get("time_unit", "month")

        # Disease - tracker names are canonical
        unified["disease_name"] = df["disease_name"]
        unified["disease_slug"] = df["disease_name"].apply(slugify)
        unified["original_disease_name"] = df["original_disease_name"]

        # Disease subtype - normalize to canonical values
        subtype_series = self._normalize_subtype(df.get("disease_subtype"))
        unified["disease_subtype"] = subtype_series
        unified["disease_subtype_slug"] = subtype_series.apply(slugify)

        # State/Geo
        unified["state"] = df["state"]
        unified["state_slug"] = df["state"].apply(slugify)

        reporting_jurisdiction = df.get("reporting_jurisdiction", df["state"])
        unified["reporting_jurisdiction"] = reporting_jurisdiction
        unified["reporting_jurisdiction_slug"] = reporting_jurisdiction.apply(slugify)

        geo_name = df.get("geo_name", df["state"])
        unified["geo_name"] = geo_name
        unified["geo_name_slug"] = geo_name.apply(slugify)

        geo_unit = df.get("geo_unit", "state")
        if isinstance(geo_unit, str):
            unified["geo_unit"] = geo_unit
            unified["geo_unit_slug"] = slugify(geo_unit)
        else:
            unified["geo_unit"] = geo_unit
            unified["geo_unit_slug"] = geo_unit.apply(slugify)

        # Age group
        age_group = self._clean_nullable(df.get("age_group"))
        unified["age_group"] = age_group
        unified["age_group_slug"] = age_group.apply(slugify)

        # Other fields
        unified["confirmation_status"] = self._clean_nullable(df.get("confirmation_status"))
        unified["outcome"] = df.get("outcome", "cases")
        unified["count"] = df["count"]

        return unified

    def _clean_nullable(self, series: pd.Series | None) -> pd.Series:
        """Clean nullable columns by converting placeholder strings to None."""
        if series is None:
            return pd.Series([None] * 0)

        placeholders = {"not specified", "unknown", "n/a", "na", ""}
        return series.apply(
            lambda x: None if pd.isna(x) or str(x).lower().strip() in placeholders else x
        )

    def _normalize_subtype(self, series: pd.Series | None) -> pd.Series:
        """Normalize disease subtype values to canonical form.

        Canonical values: A, B, C, W, X, Y, Z, unknown, unspecified
        """
        if series is None:
            return pd.Series([None] * 0)

        def normalize(x):
            if pd.isna(x) or str(x).strip() == "":
                return None
            val = str(x).lower().strip()
            # Normalize to canonical values
            normalized = SUBTYPE_NORMALIZATION.get(val, x)
            return normalized

        return series.apply(normalize)
