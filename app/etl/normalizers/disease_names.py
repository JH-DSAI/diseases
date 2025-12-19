"""
Disease name normalization.

This module provides display name mappings for diseases.
Matching/grouping is done via slugified names in the database.
"""

# Display name mapping: tracker slug → human-readable name
# Used when generating display labels from slugs
DISEASE_DISPLAY_NAMES = {
    "measles": "Measles",
    "meningococcus": "Meningococcal Disease",
    "pertussis": "Pertussis",
}


def get_display_name(disease_slug: str) -> str:
    """Get human-readable display name for a disease slug.

    Args:
        disease_slug: Slugified disease name (e.g., "meningococcus")

    Returns:
        Human-readable name, or title-cased slug if no mapping exists
    """
    if disease_slug in DISEASE_DISPLAY_NAMES:
        return DISEASE_DISPLAY_NAMES[disease_slug]

    # Fallback: convert slug to title case
    return disease_slug.replace("-", " ").title()
