"""
Disease name normalization.

This module centralizes all disease name mappings and aliases to ensure
consistent naming across data sources. It consolidates mappings from:
- Tracker disease names -> NNDSS standard names
- NNDSS internal inconsistencies (case, punctuation variations)
- Known disease aliases (same disease, different names)
"""

import re

import pandas as pd

# Mapping from tracker disease names to NNDSS standard names
# Keys are lowercase for case-insensitive matching
TRACKER_TO_NNDSS = {
    "measles": "Measles",
    "meningococcus": "Meningococcal disease",
    "pertussis": "Pertussis",
}

# Disease aliases - map variant names to canonical forms
# Applied after initial normalization to merge duplicate diseases
DISEASE_ALIASES = {
    # NNDSS internal inconsistencies (same disease, different names)
    "Hansen's Disease": "Leprosy (Hansen's Disease)",
    # Add more aliases as needed when discovered
}


def normalize_tracker_disease_name(name: str) -> str:
    """
    Normalize a tracker disease name to NNDSS standard.

    Args:
        name: Disease name from tracker data

    Returns:
        NNDSS standard disease name, or original if no mapping exists
    """
    if pd.isna(name):
        return name
    name_lower = str(name).lower()
    return TRACKER_TO_NNDSS.get(name_lower, name)


def normalize_nndss_disease_name(name: str) -> str:
    """
    Normalize an NNDSS disease name to handle inconsistencies.

    Handles:
    - Case differences: "Coccidioidomycosis, total" vs "Coccidioidomycosis, Total"
    - Comma variations: "Hepatitis, B, acute" vs "Hepatitis B, acute"
    - Apostrophe casing: "Hansen's disease" -> "Hansen's Disease"

    Args:
        name: Disease name from NNDSS data

    Returns:
        Normalized disease name
    """
    if pd.isna(name):
        return name

    name = str(name).strip()

    # Normalize "Hepatitis, B" to "Hepatitis B" (remove comma before single letter)
    name = re.sub(r",\s*([A-Za-z])\s*,", r" \1,", name)

    # Title case with proper handling of apostrophes and commas
    parts = name.split(", ")
    normalized_parts = []

    for i, part in enumerate(parts):
        if i == 0:
            # First part: title case with apostrophe fix
            titled = part.strip().title()
            # Fix apostrophe-S issue (Hansen'S -> Hansen's)
            titled = re.sub(r"'S\b", "'s", titled)
            normalized_parts.append(titled)
        else:
            # Subsequent parts: capitalize first letter only
            part = part.strip()
            if part:
                normalized_parts.append(
                    part[0].upper() + part[1:].lower() if len(part) > 1 else part.upper()
                )

    return ", ".join(normalized_parts)


def normalize_disease_name(name: str, source: str) -> str:
    """
    Normalize a disease name based on its source.

    Args:
        name: Disease name to normalize
        source: Data source ('tracker' or 'nndss')

    Returns:
        Normalized disease name
    """
    if source == "tracker":
        return normalize_tracker_disease_name(name)
    elif source == "nndss":
        return normalize_nndss_disease_name(name)
    else:
        return name


def apply_disease_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply disease aliases to a DataFrame to merge duplicate diseases.

    Args:
        df: DataFrame with 'disease_name' column

    Returns:
        DataFrame with aliases applied
    """
    df = df.copy()
    df["disease_name"] = df["disease_name"].replace(DISEASE_ALIASES)
    return df
