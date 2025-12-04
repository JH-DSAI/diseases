"""Utility functions for the disease dashboard."""

import re
import unicodedata


def to_disease_slug(name: str) -> str:
    """Generate deterministic, URL-safe slug from disease name.

    Args:
        name: The disease name to convert to a slug.

    Returns:
        A lowercase, hyphen-separated string safe for URLs, HTML IDs,
        CSS selectors, and JavaScript identifiers.

    Examples:
        >>> to_disease_slug("Measles")
        'measles'
        >>> to_disease_slug("West Nile virus disease")
        'west-nile-virus-disease'
        >>> to_disease_slug("Carbapenemase-Producing Organisms (CPO), Total")
        'carbapenemase-producing-organisms-cpo-total'
        >>> to_disease_slug("Hansen's Disease")
        'hansens-disease'
        >>> to_disease_slug("Haemophilus Influenzae, Invasive Disease, Age <5 Years")
        'haemophilus-influenzae-invasive-disease-age-5-years'
    """
    # Normalize unicode (NFC for consistency)
    s = unicodedata.normalize("NFC", name)
    # Lowercase
    s = s.lower()
    # Replace apostrophes with nothing (Hansen's → hansens)
    s = s.replace("'", "")
    # Replace any non-alphanumeric with hyphen
    s = re.sub(r"[^a-z0-9]+", "-", s)
    # Remove leading/trailing hyphens
    s = s.strip("-")
    # Collapse multiple hyphens
    s = re.sub(r"-+", "-", s)
    return s
