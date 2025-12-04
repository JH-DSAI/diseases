"""
Geographic data normalization.

This module provides state code mappings and regional classifications
for normalizing geographic data across sources.
"""

# State name to 2-letter code mapping
# Includes 50 US states, DC, and US territories
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
    # US Territories
    "AMERICAN SAMOA": "AS",
    "GUAM": "GU",
    "NORTHERN MARIANA ISLANDS": "MP",
    "PUERTO RICO": "PR",
    "VIRGIN ISLANDS": "VI",
}

# Regional aggregates in NNDSS data (not state-level)
# These should typically be excluded from state-level analyses
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


def normalize_state_code(name: str) -> str:
    """
    Convert a state name to its 2-letter code.

    Args:
        name: State name (case-insensitive)

    Returns:
        2-letter state code, or original name if not found
    """
    if not name:
        return name
    return STATE_CODES.get(str(name).upper(), name)


def is_region(name: str) -> bool:
    """
    Check if a geographic name is a regional aggregate.

    Args:
        name: Geographic name to check

    Returns:
        True if the name is a regional aggregate
    """
    if not name:
        return False
    return str(name).upper() in REGIONS


def classify_geo_unit(reporting_area: str) -> str:
    """
    Classify a reporting area as state, region, or national level.

    Args:
        reporting_area: The reporting area name from NNDSS

    Returns:
        'national', 'region', or 'state'
    """
    if not reporting_area:
        return "state"

    area_upper = str(reporting_area).upper()

    # National level records
    if area_upper in {"US RESIDENTS", "NON-US RESIDENTS", "TOTAL"}:
        return "national"

    # Regional aggregates
    if area_upper in REGIONS:
        return "region"

    # Default to state level
    return "state"
