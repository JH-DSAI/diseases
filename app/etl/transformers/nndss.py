"""
NNDSS (National Notifiable Diseases Surveillance System) data transformer.

This module handles loading and transforming CDC NNDSS weekly data
into the unified disease_data schema.

Supports both local filesystem and remote storage (Azure Blob, S3) via fsspec.
"""

import logging
import re
from datetime import datetime, timedelta

import pandas as pd

from app.etl.base import DataSourceTransformer
from app.etl.normalizers.geo import classify_geo_unit
from app.etl.normalizers.slugify import slugify
from app.etl.storage import is_remote_uri

# Map NNDSS base disease names (slugified) to tracker canonical names
NNDSS_TO_TRACKER_SLUG = {
    "meningococcal-disease": "meningococcus",
    "measles": "measles",
    "pertussis": "pertussis",
}

# Prefixes to strip from subtypes (lowercase for comparison)
SUBTYPE_PREFIXES = ["serogroup ", "serogroups "]

# Aggregate subtypes that should be null (not individual data)
# - "all serogroups" is a total row for meningococcal
# - "imported"/"indigenous" are classification metadata for measles, not subtypes
AGGREGATE_SUBTYPES = {"all serogroups", "total", "all", "imported", "indigenous"}

# Normalize NNDSS subtype names to canonical tracker values
# See docs/data-decisions.md for rationale
SUBTYPE_NORMALIZATION = {
    "other": "unspecified",
    "unknown": "unknown",
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

    Supports both local filesystem and remote storage via fsspec.
    """

    def __init__(self, source_uri: str):
        super().__init__(source_uri)
        self.mmwr_converter = MMWRWeekConverter()

    def get_source_name(self) -> str:
        return "nndss"

    def transform(self) -> pd.DataFrame:
        """
        Load and transform NNDSS data to unified schema.

        Supports both local filesystem and remote storage via fsspec.

        Returns:
            DataFrame with NNDSS data in unified schema format
        """
        # Find the latest NNDSS CSV file
        csv_file = self._find_latest_file()
        if csv_file is None:
            logger.warning(f"No NNDSS CSV files found in {self.source_uri}")
            return pd.DataFrame()

        logger.info(f"Loading NNDSS data from {csv_file}")

        # Build the full URI for pandas to read
        if is_remote_uri(self.source_uri):
            file_uri = f"az://{csv_file}"
            df = pd.read_csv(
                file_uri,
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
                storage_options=self.storage_options,
            )
        else:
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

    def _find_latest_file(self) -> str | None:
        """Find the most recent NNDSS CSV file in the source directory."""
        if not self.fs.exists(self.base_path):
            return None

        # Use fsspec glob to find files
        nndss_files = self.fs.glob(f"{self.base_path}/NNDSS_Weekly_Data_*.csv")
        if not nndss_files:
            return None

        # Return the most recent file (sorted by name, most recent first)
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
        """Parse NNDSS labels to extract base disease name and subtype.

        NNDSS labels encode subtypes after a comma:
        - "Measles, Imported" → base="Measles", subtype="Imported"
        - "Meningococcal disease, Serogroup B" → base="Meningococcal disease", subtype="B"
        - "Pertussis" → base="Pertussis", subtype=None

        Subtype processing:
        - Strip "Serogroup " / "Serogroups " prefix: "Serogroup B" → "B"
        - Set aggregate subtypes to None: "All serogroups" → None
        """
        df = df.copy()

        # Store original name before any transformation
        df["original_disease_name"] = df["Label"]

        # Parse labels into (base_name, subtype)
        parsed = df["Label"].apply(self._parse_nndss_label)
        df["disease_name"] = parsed.apply(lambda x: x[0])
        df["disease_subtype"] = parsed.apply(lambda x: x[1])

        return df

    def _parse_nndss_label(self, label: str) -> tuple[str, str | None]:
        """Parse 'Disease, Subtype info' into (base_name, subtype).

        Args:
            label: NNDSS disease label (e.g., "Meningococcal disease, Serogroup B")

        Returns:
            Tuple of (base_name, subtype) where subtype may be None
        """
        if pd.isna(label):
            return (None, None)

        label = str(label).strip()

        if "," not in label:
            return (label, None)

        parts = label.split(",", 1)
        base_name = parts[0].strip()
        subtype_raw = parts[1].strip() if len(parts) > 1 else None

        if subtype_raw:
            # Check for aggregate subtypes (should be null)
            if subtype_raw.lower() in AGGREGATE_SUBTYPES:
                return (base_name, None)

            # Strip known prefixes from subtype ("Serogroup B" → "B")
            subtype_lower = subtype_raw.lower()
            for prefix in SUBTYPE_PREFIXES:
                if subtype_lower.startswith(prefix):
                    subtype_raw = subtype_raw[len(prefix) :]
                    break

            # Strip "serogroup(s)" suffix ("Other serogroups" → "Other")
            subtype_raw = re.sub(
                r"\s*serogroups?\s*$", "", subtype_raw, flags=re.IGNORECASE
            ).strip()

            # Normalize to canonical values ("Other" → "unspecified")
            subtype_raw = SUBTYPE_NORMALIZATION.get(subtype_raw.lower(), subtype_raw)

        return (base_name, subtype_raw if subtype_raw else None)

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
        """Map NNDSS fields to the unified disease_data schema.

        Maps NNDSS disease names to tracker canonical names for consistency.
        All dimension columns get corresponding _slug columns for matching.
        """
        unified = pd.DataFrame()

        # Date/time fields
        unified["report_period_start"] = df["report_period_start"]
        unified["report_period_end"] = df["report_period_end"]
        unified["date_type"] = "mmwr"
        unified["time_unit"] = "week"

        # Disease - map NNDSS base names to tracker canonical names
        # Both disease_name and disease_slug use tracker canonical form for consistency
        base_slugs = df["disease_name"].apply(slugify)
        unified["disease_slug"] = base_slugs.apply(
            lambda s: NNDSS_TO_TRACKER_SLUG.get(s, s) if s else None
        )
        # disease_name uses the canonical slug (tracker names are lowercase)
        unified["disease_name"] = unified["disease_slug"]
        unified["original_disease_name"] = df["original_disease_name"]

        # Disease subtype
        unified["disease_subtype"] = df["disease_subtype"]
        unified["disease_subtype_slug"] = df["disease_subtype"].apply(slugify)

        # State/Geo
        unified["state"] = df["state"]
        unified["state_slug"] = df["state"].apply(slugify)

        unified["reporting_jurisdiction"] = df["state"]
        unified["reporting_jurisdiction_slug"] = df["state"].apply(slugify)

        unified["geo_name"] = df["Reporting Area"]
        unified["geo_name_slug"] = df["Reporting Area"].apply(slugify)

        unified["geo_unit"] = df["geo_unit"]
        unified["geo_unit_slug"] = df["geo_unit"].apply(slugify)

        # Age group - NNDSS weekly data doesn't include age groups
        unified["age_group"] = None
        unified["age_group_slug"] = None

        # Other fields
        unified["confirmation_status"] = None
        unified["outcome"] = "cases"
        unified["count"] = df["count"]

        return unified
