"""Tests for ETL normalizer functions."""

import pandas as pd

from app.etl.normalizers.disease_names import get_display_name
from app.etl.normalizers.geo import (
    NATIONAL_SLUGS,
    REGION_SLUGS,
    classify_geo_unit,
)
from app.etl.normalizers.slugify import slugify


class TestSlugify:
    """Tests for slugify function."""

    def test_basic_slugify(self):
        """Test basic string slugification."""
        assert slugify("Hello World") == "hello-world"
        assert slugify("Meningococcal disease") == "meningococcal-disease"

    def test_removes_punctuation(self):
        """Test punctuation is removed."""
        assert slugify("U.S. Residents") == "us-residents"
        assert slugify("Hansen's Disease") == "hansens-disease"
        assert slugify("Test, with, commas") == "test-with-commas"

    def test_handles_case(self):
        """Test case normalization."""
        assert slugify("OTHER") == "other"
        assert slugify("Other") == "other"
        assert slugify("other") == "other"

    def test_collapses_whitespace(self):
        """Test multiple spaces collapse to single hyphen."""
        assert slugify("Hello   World") == "hello-world"
        assert slugify("  padded  ") == "padded"

    def test_underscores_to_hyphens(self):
        """Test underscores become hyphens."""
        assert slugify("hello_world") == "hello-world"

    def test_none_returns_none(self):
        """Test None returns None."""
        assert slugify(None) is None

    def test_nan_returns_none(self):
        """Test NaN returns None."""
        assert slugify(pd.NA) is None

    def test_empty_returns_none(self):
        """Test empty string returns None."""
        assert slugify("") is None
        assert slugify("   ") is None

    def test_state_codes(self):
        """Test state codes slugify correctly."""
        assert slugify("CA") == "ca"
        assert slugify("NY") == "ny"
        assert slugify("NYC") == "nyc"

    def test_serogroups(self):
        """Test serogroup slugification."""
        assert slugify("B") == "b"
        assert slugify("ACWY") == "acwy"
        assert slugify("Other") == "other"


class TestClassifyGeoUnit:
    """Tests for classify_geo_unit function."""

    def test_national_level(self):
        """Test national level classifications."""
        assert classify_geo_unit("US RESIDENTS") == "national"
        assert classify_geo_unit("NON-US RESIDENTS") == "national"
        assert classify_geo_unit("TOTAL") == "national"

    def test_national_with_punctuation(self):
        """Test national level with punctuation variations."""
        # The bug case - periods and different casing
        assert classify_geo_unit("U.S. Residents") == "national"
        assert classify_geo_unit("U.S.Residents") == "national"
        assert classify_geo_unit("us residents") == "national"

    def test_region_level(self):
        """Test region level classifications."""
        assert classify_geo_unit("PACIFIC") == "region"
        assert classify_geo_unit("NEW ENGLAND") == "region"
        assert classify_geo_unit("MOUNTAIN") == "region"
        assert classify_geo_unit("pacific") == "region"

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


class TestGetDisplayName:
    """Tests for get_display_name function."""

    def test_known_disease(self):
        """Test known disease mapping."""
        assert get_display_name("meningococcus") == "Meningococcal Disease"
        assert get_display_name("measles") == "Measles"
        assert get_display_name("pertussis") == "Pertussis"

    def test_unknown_disease_titlecase(self):
        """Test unknown disease gets title-cased."""
        assert get_display_name("unknown-disease") == "Unknown Disease"
        assert get_display_name("some-new-disease") == "Some New Disease"


class TestSlugConstants:
    """Tests for slug constant sets."""

    def test_national_slugs_are_slugified(self):
        """Test national slugs are properly formatted."""
        for slug in NATIONAL_SLUGS:
            assert slug == slug.lower()
            assert " " not in slug
            assert "." not in slug

    def test_region_slugs_are_slugified(self):
        """Test region slugs are properly formatted."""
        for slug in REGION_SLUGS:
            assert slug == slug.lower()
            assert " " not in slug
            assert "." not in slug

    def test_expected_national_slugs(self):
        """Test expected national slugs are present."""
        assert "us-residents" in NATIONAL_SLUGS
        assert "non-us-residents" in NATIONAL_SLUGS
        assert "total" in NATIONAL_SLUGS

    def test_expected_region_slugs(self):
        """Test expected region slugs are present."""
        assert "pacific" in REGION_SLUGS
        assert "new-england" in REGION_SLUGS
        assert "mountain" in REGION_SLUGS
