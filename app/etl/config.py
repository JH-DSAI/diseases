"""
ETL configuration.

This module provides explicit configuration for data source transformers.
To add a new data source, import its transformer and add it to TRANSFORMERS.
"""

from typing import TYPE_CHECKING

from app.etl.transformers.nndss import NNDSSTransformer
from app.etl.transformers.tracker import TrackerTransformer

if TYPE_CHECKING:
    from app.etl.base import DataSourceTransformer

# Explicit mapping of source names to transformer classes
# To add a new source: import the transformer and add it here
TRANSFORMERS: dict[str, type["DataSourceTransformer"]] = {
    "tracker": TrackerTransformer,
    "nndss": NNDSSTransformer,
}


def get_transformer(name: str) -> type["DataSourceTransformer"]:
    """
    Get transformer class by source name.

    Args:
        name: Data source name (e.g., 'tracker', 'nndss')

    Returns:
        Transformer class for the specified source

    Raises:
        ValueError: If source name is not configured
    """
    if name not in TRANSFORMERS:
        available = ", ".join(sorted(TRANSFORMERS.keys()))
        raise ValueError(f"Unknown data source: '{name}'. Available sources: {available}")
    return TRANSFORMERS[name]


def list_sources() -> list[str]:
    """
    List all configured data source names.

    Returns:
        List of source names in alphabetical order
    """
    return sorted(TRANSFORMERS.keys())
