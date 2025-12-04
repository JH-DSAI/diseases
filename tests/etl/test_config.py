"""Tests for ETL configuration."""

import pytest

from app.etl.config import get_transformer, list_sources
from app.etl.transformers.nndss import NNDSSTransformer
from app.etl.transformers.tracker import TrackerTransformer


class TestGetTransformer:
    """Tests for get_transformer function."""

    def test_tracker_transformer(self):
        """Test getting tracker transformer."""
        assert get_transformer("tracker") is TrackerTransformer

    def test_nndss_transformer(self):
        """Test getting NNDSS transformer."""
        assert get_transformer("nndss") is NNDSSTransformer

    def test_invalid_source_raises(self):
        """Test invalid source raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_transformer("invalid_source")
        assert "Unknown data source" in str(exc_info.value)
        assert "invalid_source" in str(exc_info.value)


class TestListSources:
    """Tests for list_sources function."""

    def test_returns_sorted_list(self):
        """Test sources are returned in sorted order."""
        sources = list_sources()
        assert sources == sorted(sources)

    def test_contains_expected_sources(self):
        """Test expected sources are present."""
        sources = list_sources()
        assert "tracker" in sources
        assert "nndss" in sources
