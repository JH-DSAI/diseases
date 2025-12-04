"""Tests for ETL normalizer functions."""

import pandas as pd

from app.etl.normalizers.disease_names import (
    apply_disease_aliases,
    normalize_disease_name,
    normalize_nndss_disease_name,
    normalize_tracker_disease_name,
)
from app.etl.normalizers.geo import (
    classify_geo_unit,
    is_region,
    normalize_state_code,
)


class TestNormalizeStateCode:
    """Tests for normalize_state_code function."""

    def test_valid_state_name(self):
        """Test conversion of full state name to code."""
        assert normalize_state_code("California") == "CA"
        assert normalize_state_code("CALIFORNIA") == "CA"
        assert normalize_state_code("california") == "CA"

    def test_already_code(self):
        """Test that state codes pass through."""
        assert normalize_state_code("CA") == "CA"
        assert normalize_state_code("NY") == "NY"

    def test_empty_returns_empty(self):
        """Test empty string returns empty."""
        assert normalize_state_code("") == ""

    def test_none_returns_none(self):
        """Test None returns None."""
        assert normalize_state_code(None) is None

    def test_unknown_returns_original(self):
        """Test unknown names pass through."""
        assert normalize_state_code("Unknown Place") == "Unknown Place"


class TestIsRegion:
    """Tests for is_region function."""

    def test_region_names(self):
        """Test regional aggregate names."""
        assert is_region("US RESIDENTS") is True
        assert is_region("PACIFIC") is True
        assert is_region("NEW ENGLAND") is True
        assert is_region("TOTAL") is True

    def test_state_names(self):
        """Test state names are not regions."""
        assert is_region("California") is False
        assert is_region("CA") is False
        assert is_region("New York") is False

    def test_empty_returns_false(self):
        """Test empty string returns False."""
        assert is_region("") is False

    def test_none_returns_false(self):
        """Test None returns False."""
        assert is_region(None) is False


class TestClassifyGeoUnit:
    """Tests for classify_geo_unit function."""

    def test_national_level(self):
        """Test national level classifications."""
        assert classify_geo_unit("US RESIDENTS") == "national"
        assert classify_geo_unit("NON-US RESIDENTS") == "national"
        assert classify_geo_unit("TOTAL") == "national"

    def test_region_level(self):
        """Test region level classifications."""
        assert classify_geo_unit("PACIFIC") == "region"
        assert classify_geo_unit("NEW ENGLAND") == "region"
        assert classify_geo_unit("MOUNTAIN") == "region"

    def test_state_level(self):
        """Test state level classifications."""
        assert classify_geo_unit("California") == "state"
        assert classify_geo_unit("CA") == "state"
        assert classify_geo_unit("New York City") == "state"

    def test_empty_returns_state(self):
        """Test empty string defaults to state."""
        assert classify_geo_unit("") == "state"

    def test_none_returns_state(self):
        """Test None defaults to state."""
        assert classify_geo_unit(None) == "state"


class TestNormalizeTrackerDiseaseName:
    """Tests for normalize_tracker_disease_name function."""

    def test_mapped_disease(self):
        """Test diseases with known mappings."""
        assert normalize_tracker_disease_name("measles") == "Measles"
        assert normalize_tracker_disease_name("pertussis") == "Pertussis"

    def test_unmapped_disease(self):
        """Test diseases without mappings pass through."""
        assert normalize_tracker_disease_name("Unknown Disease") == "Unknown Disease"

    def test_nan_returns_nan(self):
        """Test NaN values pass through."""
        result = normalize_tracker_disease_name(pd.NA)
        assert pd.isna(result)


class TestNormalizeNndssDiseaseName:
    """Tests for normalize_nndss_disease_name function."""

    def test_title_case(self):
        """Test title case normalization."""
        assert normalize_nndss_disease_name("measles") == "Measles"

    def test_apostrophe_fix(self):
        """Test apostrophe-S fix (Hansen'S -> Hansen's)."""
        assert "Hansen's" in normalize_nndss_disease_name("hansen's disease")

    def test_comma_parts(self):
        """Test comma-separated parts handling."""
        result = normalize_nndss_disease_name("hepatitis, acute")
        assert result == "Hepatitis, Acute"

    def test_nan_returns_nan(self):
        """Test NaN values pass through."""
        result = normalize_nndss_disease_name(pd.NA)
        assert pd.isna(result)

    def test_short_string(self):
        """Test single character handling."""
        assert normalize_nndss_disease_name("a") == "A"


class TestNormalizeDiseaseName:
    """Tests for normalize_disease_name function."""

    def test_tracker_source(self):
        """Test tracker source normalization."""
        assert normalize_disease_name("measles", "tracker") == "Measles"

    def test_nndss_source(self):
        """Test NNDSS source normalization."""
        assert normalize_disease_name("measles", "nndss") == "Measles"

    def test_unknown_source(self):
        """Test unknown source passes through."""
        assert normalize_disease_name("measles", "unknown") == "measles"


class TestApplyDiseaseAliases:
    """Tests for apply_disease_aliases function."""

    def test_applies_aliases(self):
        """Test aliases are applied."""
        df = pd.DataFrame({"disease_name": ["Hansen's Disease", "Measles"]})
        result = apply_disease_aliases(df)
        assert result["disease_name"].iloc[0] == "Leprosy (Hansen's Disease)"
        assert result["disease_name"].iloc[1] == "Measles"

    def test_preserves_unmatched(self):
        """Test unmatched names are preserved."""
        df = pd.DataFrame({"disease_name": ["Unknown Disease"]})
        result = apply_disease_aliases(df)
        assert result["disease_name"].iloc[0] == "Unknown Disease"
