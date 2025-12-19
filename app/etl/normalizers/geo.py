"""
Geographic data normalization.

This module provides geographic classification using slugified values
for consistent matching across data sources.
"""

from app.etl.normalizers.slugify import slugify

# National-level reporting areas (slugified)
# Includes variants for different formatting (e.g., "U.S.Residents" vs "US RESIDENTS")
NATIONAL_SLUGS = {
    "us-residents",
    "usresidents",  # "U.S.Residents" without space
    "non-us-residents",
    "nonusresidents",  # "NON-U.S.RESIDENTS" without spaces
    "total",
}

# Regional aggregates in NNDSS data (slugified)
REGION_SLUGS = {
    "new-england",
    "middle-atlantic",
    "east-north-central",
    "west-north-central",
    "south-atlantic",
    "east-south-central",
    "west-south-central",
    "mountain",
    "pacific",
    "us-territories",
}


def classify_geo_unit(reporting_area: str) -> str:
    """
    Classify a reporting area as state, region, or national level.

    Uses slugified values for consistent matching regardless of
    casing, punctuation, or spacing variations.

    Args:
        reporting_area: The reporting area name from NNDSS

    Returns:
        'national', 'region', or 'state'
    """
    if not reporting_area:
        return "state"

    slug = slugify(reporting_area)

    if slug in NATIONAL_SLUGS:
        return "national"

    if slug in REGION_SLUGS:
        return "region"

    return "state"
