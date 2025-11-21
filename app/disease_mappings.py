"""
Disease name mapping between tracker data and NNDSS (CDC standard).

This module provides mappings to normalize disease names from the state tracker
data to match the CDC's NNDSS standard nomenclature. NNDSS names are treated
as the canonical reference.
"""

# Mapping from tracker disease names to NNDSS (CDC) standard names
TRACKER_TO_NNDSS = {
    "measles": "Measles",
    "meningococcus": "Meningococcal disease",
    "pertussis": "Pertussis",
}

# Reverse mapping for convenience
NNDSS_TO_TRACKER = {v: k for k, v in TRACKER_TO_NNDSS.items()}


def normalize_disease_name(tracker_name: str) -> str:
    """
    Convert a tracker disease name to the NNDSS standard name.

    Args:
        tracker_name: Disease name from tracker data (e.g., 'measles')

    Returns:
        NNDSS standard disease name (e.g., 'Measles')

    Raises:
        KeyError: If the disease name is not found in the mapping
    """
    return TRACKER_TO_NNDSS[tracker_name.lower()]


def get_all_nndss_names() -> list[str]:
    """Get a list of all NNDSS standard disease names."""
    return list(TRACKER_TO_NNDSS.values())


def get_all_tracker_names() -> list[str]:
    """Get a list of all tracker disease names."""
    return list(TRACKER_TO_NNDSS.keys())
