"""
Slugify utility for canonical normalization.

This module provides a consistent way to convert any string value to a
machine-friendly slug format for matching and grouping across data sources.
"""

import re

import pandas as pd


def slugify(value: str | None) -> str | None:
    """Convert any string to a canonical machine-friendly slug.

    Transformations:
    - Lowercase
    - Strip punctuation (periods, commas, apostrophes, etc.)
    - Replace whitespace/underscores with hyphens
    - Collapse multiple hyphens
    - Strip leading/trailing hyphens

    Examples:
        >>> slugify("Meningococcal disease")
        'meningococcal-disease'
        >>> slugify("U.S. Residents")
        'us-residents'
        >>> slugify("OTHER")
        'other'
        >>> slugify("Serogroup B")
        'serogroup-b'
        >>> slugify(None)
        None

    Args:
        value: String to slugify, or None

    Returns:
        Slugified string, or None if input is None/empty
    """
    if value is None or pd.isna(value):
        return None

    value = str(value).lower().strip()

    # Remove punctuation (keep alphanumeric, whitespace, hyphens)
    value = re.sub(r"[^\w\s-]", "", value)

    # Replace whitespace and underscores with hyphens
    value = re.sub(r"[\s_]+", "-", value)

    # Collapse multiple hyphens
    value = re.sub(r"-+", "-", value)

    # Strip leading/trailing hyphens
    value = value.strip("-")

    return value if value else None
