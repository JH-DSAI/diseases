"""
NNDSS data loader and transformer.

This module handles loading and transforming CDC NNDSS (National Notifiable
Diseases Surveillance System) weekly data into the unified disease_data schema.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


class MMWRWeekConverter:
    """Converts MMWR (Morbidity and Mortality Weekly Report) weeks to date ranges."""

    @staticmethod
    def get_mmwr_week_start(year: int, week: int) -> datetime:
        """
        Calculate the start date of an MMWR week.

        MMWR weeks start on Sunday. Week 1 is the first week of the year
        that has at least four days in the year (following ISO-like rules
        adapted for Sunday start).

        Args:
            year: MMWR year
            week: MMWR week number (1-53)

        Returns:
            datetime object for the Sunday starting that MMWR week
        """
        # Find January 1st of the year
        jan1 = datetime(year, 1, 1)

        # Find the first Sunday on or after January 1st
        # Sunday is weekday 6 in Python's datetime (Monday=0)
        days_until_sunday = (6 - jan1.weekday()) % 7
        first_sunday = jan1 + timedelta(days=days_until_sunday)

        # If Jan 1 is Sun, Mon, Tue, or Wed, week 1 starts on the first Sunday
        # Otherwise, week 1 starts on the next Sunday after Jan 1
        if jan1.weekday() <= 3:  # Sun (6), Mon (0), Tue (1), Wed (2)
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
        Calculate the end date of an MMWR week.

        Args:
            year: MMWR year
            week: MMWR week number (1-53)

        Returns:
            datetime object for the Saturday ending that MMWR week
        """
        start = MMWRWeekConverter.get_mmwr_week_start(year, week)
        return start + timedelta(days=6)


class NNDSSTransformer:
    """Transforms NNDSS CSV data into the unified disease_data schema."""

    # Regional aggregates to identify (not state-level)
    REGIONS = {
        "US RESIDENTS",
        "NON-US RESIDENTS",
        "TOTAL",
        "NEW ENGLAND",
        "MIDDLE ATLANTIC",
        "EAST NORTH CENTRAL",
        "WEST NORTH CENTRAL",
        "SOUTH ATLANTIC",
        "EAST SOUTH CENTRAL",
        "WEST SOUTH CENTRAL",
        "MOUNTAIN",
        "PACIFIC",
        "US TERRITORIES",
    }

    # State name to 2-letter code mapping
    STATE_CODES = {
        "ALABAMA": "AL",
        "ALASKA": "AK",
        "ARIZONA": "AZ",
        "ARKANSAS": "AR",
        "CALIFORNIA": "CA",
        "COLORADO": "CO",
        "CONNECTICUT": "CT",
        "DELAWARE": "DE",
        "FLORIDA": "FL",
        "GEORGIA": "GA",
        "HAWAII": "HI",
        "IDAHO": "ID",
        "ILLINOIS": "IL",
        "INDIANA": "IN",
        "IOWA": "IA",
        "KANSAS": "KS",
        "KENTUCKY": "KY",
        "LOUISIANA": "LA",
        "MAINE": "ME",
        "MARYLAND": "MD",
        "MASSACHUSETTS": "MA",
        "MICHIGAN": "MI",
        "MINNESOTA": "MN",
        "MISSISSIPPI": "MS",
        "MISSOURI": "MO",
        "MONTANA": "MT",
        "NEBRASKA": "NE",
        "NEVADA": "NV",
        "NEW HAMPSHIRE": "NH",
        "NEW JERSEY": "NJ",
        "NEW MEXICO": "NM",
        "NEW YORK": "NY",
        "NEW YORK CITY": "NYC",
        "NORTH CAROLINA": "NC",
        "NORTH DAKOTA": "ND",
        "OHIO": "OH",
        "OKLAHOMA": "OK",
        "OREGON": "OR",
        "PENNSYLVANIA": "PA",
        "RHODE ISLAND": "RI",
        "SOUTH CAROLINA": "SC",
        "SOUTH DAKOTA": "SD",
        "TENNESSEE": "TN",
        "TEXAS": "TX",
        "UTAH": "UT",
        "VERMONT": "VT",
        "VIRGINIA": "VA",
        "WASHINGTON": "WA",
        "WEST VIRGINIA": "WV",
        "WISCONSIN": "WI",
        "WYOMING": "WY",
        "DISTRICT OF COLUMBIA": "DC",
        "AMERICAN SAMOA": "AS",
        "GUAM": "GU",
        "NORTHERN MARIANA ISLANDS": "MP",
        "PUERTO RICO": "PR",
        "VIRGIN ISLANDS": "VI",
    }

    def __init__(self, csv_path: Path):
        """
        Initialize the NNDSS transformer.

        Args:
            csv_path: Path to the NNDSS CSV file
        """
        self.csv_path = csv_path
        self.mmwr_converter = MMWRWeekConverter()

    def load_and_transform(self) -> pd.DataFrame:
        """
        Load the NNDSS CSV and transform it to the unified schema.

        Returns:
            DataFrame with transformed data matching disease_data schema
        """
        logger.info(f"Loading NNDSS data from {self.csv_path}")

        # Read CSV with proper handling of empty values
        df = pd.read_csv(
            self.csv_path,
            dtype={
                "Reporting Area": str,
                "Current MMWR Year": "Int64",
                "MMWR WEEK": "Int64",
                "Label": str,
                "Current week": str,  # Keep as string initially for cleaning
                "LOCATION1": str,
                "LOCATION2": str,
            },
            na_values=["", " "],
            keep_default_na=True,
        )

        logger.info(f"Loaded {len(df)} raw NNDSS records")

        # Transform the data
        df = self._classify_geo_unit(df)
        df = self._parse_dates(df)
        df = self._clean_case_counts(df)
        df = self._normalize_disease_names(df)
        df = self._create_state_codes(df)
        df = self._map_to_unified_schema(df)

        # Filter out rows with no case counts
        df = df[df["count"].notna()]

        logger.info(f"Transformed to {len(df)} records in unified schema")

        return df

    def _classify_geo_unit(self, df: pd.DataFrame) -> pd.DataFrame:
        """Classify records as state, region, or national level."""
        df = df.copy()

        # Vectorized classification - much faster than apply()
        # Default to state
        df["geo_unit"] = "state"

        # Mark regions
        df.loc[df["Reporting Area"].isin(self.REGIONS), "geo_unit"] = "region"

        # Mark national level (overrides region)
        national_areas = ["US RESIDENTS", "NON-US RESIDENTS", "TOTAL"]
        df.loc[df["Reporting Area"].isin(national_areas), "geo_unit"] = "national"

        return df

    def _parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert MMWR year/week to date ranges."""
        df = df.copy()

        # Vectorized approach: compute dates for unique (year, week) combinations
        # then merge back. This is much faster than computing for every row.
        unique_weeks = (
            df[["Current MMWR Year", "MMWR WEEK"]]
            .drop_duplicates()
            .dropna()
            .copy()
        )

        # Compute dates for each unique combination
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
        df = df.merge(
            unique_weeks,
            on=["Current MMWR Year", "MMWR WEEK"],
            how="left"
        )

        return df

    def _clean_case_counts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and convert case count data to integers."""
        df = df.copy()

        # Vectorized string operations - much faster than apply()
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
        """
        Normalize disease names and extract subtypes.

        Stores the original NNDSS name and creates a normalized version.
        """
        df = df.copy()

        # Store original name
        df["original_disease_name"] = df["Label"]

        # For now, use the Label as-is for disease_name
        # Subtype extraction can be added later if needed
        df["disease_name"] = df["Label"].str.strip()
        df["disease_subtype"] = None  # NNDSS doesn't provide subtypes in same granularity

        return df

    def _create_state_codes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert state names to 2-letter codes."""
        df = df.copy()

        # Vectorized state code assignment - much faster than apply()
        # Default: use reporting area as-is
        df["state"] = df["Reporting Area"]

        # For state-level records, map to state codes
        state_mask = df["geo_unit"] == "state"
        df.loc[state_mask, "state"] = (
            df.loc[state_mask, "Reporting Area"]
            .str.upper()
            .map(self.STATE_CODES)
            .fillna(df.loc[state_mask, "Reporting Area"])
        )

        # For regions, use LOCATION2 if available, otherwise reporting area
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

        # Required fields from tracker schema
        unified["report_period_start"] = df["report_period_start"]
        unified["report_period_end"] = df["report_period_end"]
        unified["date_type"] = "mmwr"
        unified["time_unit"] = "week"
        unified["disease_name"] = df["disease_name"]
        unified["disease_subtype"] = df["disease_subtype"]
        unified["state"] = df["state"]
        unified["reporting_jurisdiction"] = df["state"]  # Same as state for NNDSS
        unified["geo_name"] = df["Reporting Area"]
        unified["geo_unit"] = df["geo_unit"]
        unified["age_group"] = None  # NNDSS weekly data doesn't include age groups
        unified["confirmation_status"] = None  # Not specified in NNDSS weekly data
        unified["outcome"] = "cases"
        unified["count"] = df["count"]

        # Metadata fields
        unified["data_source"] = "nndss"
        unified["original_disease_name"] = df["original_disease_name"]

        return unified


def load_nndss_data(csv_path: Path) -> pd.DataFrame:
    """
    Load and transform NNDSS data from CSV file.

    Args:
        csv_path: Path to NNDSS CSV file

    Returns:
        DataFrame with transformed data

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV format is invalid
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"NNDSS CSV not found: {csv_path}")

    transformer = NNDSSTransformer(csv_path)
    return transformer.load_and_transform()
