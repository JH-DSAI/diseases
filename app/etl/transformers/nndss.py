"""
NNDSS (National Notifiable Diseases Surveillance System) data transformer.

This module handles loading and transforming CDC NNDSS weekly data
into the unified disease_data schema.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from app.etl.base import DataSourceTransformer
from app.etl.normalizers.disease_names import normalize_nndss_disease_name
from app.etl.normalizers.geo import STATE_CODES, classify_geo_unit

logger = logging.getLogger(__name__)


class MMWRWeekConverter:
    """
    Converts MMWR (Morbidity and Mortality Weekly Report) weeks to date ranges.

    MMWR weeks are the CDC's epidemiological week standard, starting on Sunday.
    """

    @staticmethod
    def get_mmwr_week_start(year: int, week: int) -> datetime:
        """
        Calculate the start date (Sunday) of an MMWR week.

        MMWR weeks start on Sunday. Week 1 is the first week of the year
        that has at least four days in the year.

        Args:
            year: MMWR year
            week: MMWR week number (1-53)

        Returns:
            datetime for the Sunday starting that MMWR week
        """
        jan1 = datetime(year, 1, 1)

        # Find the first Sunday on or after January 1st
        days_until_sunday = (6 - jan1.weekday()) % 7
        first_sunday = jan1 + timedelta(days=days_until_sunday)

        # If Jan 1 is Sun, Mon, Tue, or Wed, week 1 starts on the first Sunday
        # Otherwise, week 1 starts on the next Sunday after Jan 1
        if jan1.weekday() <= 3:  # Sun (6->0 after mod), Mon (0), Tue (1), Wed (2)
            week1_start = first_sunday
        else:
            # Jan 1 is Thu, Fri, or Sat - week 1 starts the following Sunday
            week1_start = first_sunday + timedelta(days=7)

        # Calculate the target week's start date
        target_week_start = week1_start + timedelta(weeks=(week - 1))
        return target_week_start

    @staticmethod
    def get_mmwr_week_end(year: int, week: int) -> datetime:
        """
        Calculate the end date (Saturday) of an MMWR week.

        Args:
            year: MMWR year
            week: MMWR week number (1-53)

        Returns:
            datetime for the Saturday ending that MMWR week
        """
        start = MMWRWeekConverter.get_mmwr_week_start(year, week)
        return start + timedelta(days=6)


class NNDSSTransformer(DataSourceTransformer):
    """
    Transformer for CDC NNDSS weekly surveillance data.

    Handles NNDSS-specific transformations:
    - MMWR week to date conversion
    - Geographic level classification (state/region/national)
    - Case count cleaning (handling "-", "N", etc.)
    - State name to code mapping
    - Disease name normalization
    """

    def __init__(self, source_path: Path):
        super().__init__(source_path)
        self.mmwr_converter = MMWRWeekConverter()

    def get_source_name(self) -> str:
        return "nndss"

    def transform(self) -> pd.DataFrame:
        """
        Load and transform NNDSS data to unified schema.

        Returns:
            DataFrame with NNDSS data in unified schema format
        """
        # Find the latest NNDSS CSV file
        csv_file = self._find_latest_file()
        if csv_file is None:
            logger.warning(f"No NNDSS CSV files found in {self.source_path}")
            return pd.DataFrame()

        logger.info(f"Loading NNDSS data from {csv_file}")

        # Load CSV with proper handling of empty values
        df = pd.read_csv(
            csv_file,
            dtype={
                "Reporting Area": str,
                "Current MMWR Year": "Int64",
                "MMWR WEEK": "Int64",
                "Label": str,
                "Current week": str,
                "LOCATION1": str,
                "LOCATION2": str,
            },
            na_values=["", " "],
            keep_default_na=True,
            low_memory=False,
        )

        logger.info(f"Loaded {len(df)} raw NNDSS records")

        # Apply transformations in sequence
        df = self._classify_geo_unit(df)
        df = self._parse_dates(df)
        df = self._clean_case_counts(df)
        df = self._normalize_disease_names(df)
        df = self._create_state_codes(df)
        df = self._map_to_unified_schema(df)

        # Filter out rows with no case counts
        df = df[df["count"].notna()]

        # Filter to state-level records only (exclude regional aggregates and national totals)
        pre_filter_count = len(df)
        df = df[df["geo_unit"] == "state"]
        logger.info(
            f"Filtered {pre_filter_count - len(df)} non-state records (regions, national totals)"
        )

        logger.info(f"Transformed to {len(df)} records")
        return df

    def _find_latest_file(self) -> Path | None:
        """Find the most recent NNDSS CSV file in the source directory."""
        if not self.source_path.exists():
            return None

        nndss_files = list(self.source_path.glob("NNDSS_Weekly_Data_*.csv"))
        if not nndss_files:
            return None

        # Return the most recent file (sorted by name)
        return sorted(nndss_files, reverse=True)[0]

    def _classify_geo_unit(self, df: pd.DataFrame) -> pd.DataFrame:
        """Classify records as state, region, or national level."""
        df = df.copy()
        df["geo_unit"] = df["Reporting Area"].apply(classify_geo_unit)
        return df

    def _parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert MMWR year/week to date ranges."""
        df = df.copy()

        # Compute dates for unique (year, week) combinations, then merge back
        unique_weeks = df[["Current MMWR Year", "MMWR WEEK"]].drop_duplicates().dropna().copy()

        starts = []
        ends = []
        for _, row in unique_weeks.iterrows():
            try:
                year = int(row["Current MMWR Year"])
                week = int(row["MMWR WEEK"])
                start = self.mmwr_converter.get_mmwr_week_start(year, week)
                end = self.mmwr_converter.get_mmwr_week_end(year, week)
                starts.append(start)
                ends.append(end)
            except (ValueError, TypeError):
                starts.append(pd.NaT)
                ends.append(pd.NaT)

        unique_weeks["report_period_start"] = starts
        unique_weeks["report_period_end"] = ends

        # Merge back to original dataframe
        df = df.merge(unique_weeks, on=["Current MMWR Year", "MMWR WEEK"], how="left")

        return df

    def _clean_case_counts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and convert case count data to integers."""
        df = df.copy()

        # Start with the current week column
        counts = df["Current week"].astype(str)

        # Replace common non-numeric indicators with empty string
        counts = counts.replace(["nan", "-", "", " "], "")

        # Extract only digits using regex
        counts = counts.str.replace(r"\D", "", regex=True)

        # Convert to numeric, empty strings become NaN
        counts = counts.replace("", pd.NA)
        df["count"] = pd.to_numeric(counts, errors="coerce")

        return df

    def _normalize_disease_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize disease names to handle NNDSS inconsistencies."""
        df = df.copy()

        # Store original name
        df["original_disease_name"] = df["Label"]

        # Apply normalization
        df["disease_name"] = df["Label"].apply(normalize_nndss_disease_name)

        # Disease subtype not provided in NNDSS weekly data
        df["disease_subtype"] = None

        return df

    def _create_state_codes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert state names to 2-letter codes."""
        df = df.copy()

        # Default: use reporting area as-is
        df["state"] = df["Reporting Area"]

        # For state-level records, map to state codes
        state_mask = df["geo_unit"] == "state"
        df.loc[state_mask, "state"] = (
            df.loc[state_mask, "Reporting Area"]
            .str.upper()
            .map(STATE_CODES)
            .fillna(df.loc[state_mask, "Reporting Area"])
        )

        # For regions, use LOCATION2 if available
        region_mask = df["geo_unit"] == "region"
        df.loc[region_mask, "state"] = df.loc[region_mask, "LOCATION2"].fillna(
            df.loc[region_mask, "Reporting Area"]
        )

        # For national level, set to "US"
        national_mask = df["geo_unit"] == "national"
        df.loc[national_mask, "state"] = "US"

        return df

    def _map_to_unified_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map NNDSS fields to the unified disease_data schema."""
        unified = pd.DataFrame()

        unified["report_period_start"] = df["report_period_start"]
        unified["report_period_end"] = df["report_period_end"]
        unified["date_type"] = "mmwr"
        unified["time_unit"] = "week"
        unified["disease_name"] = df["disease_name"]
        unified["disease_subtype"] = df["disease_subtype"]
        unified["state"] = df["state"]
        unified["reporting_jurisdiction"] = df["state"]
        unified["geo_name"] = df["Reporting Area"]
        unified["geo_unit"] = df["geo_unit"]
        unified["age_group"] = None  # NNDSS weekly data doesn't include age groups
        unified["confirmation_status"] = None
        unified["outcome"] = "cases"
        unified["count"] = df["count"]
        unified["original_disease_name"] = df["original_disease_name"]

        return unified
