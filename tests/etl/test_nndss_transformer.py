"""Tests for NNDSS data transformation."""

from pathlib import Path

import pandas as pd

from app.etl.transformers.nndss import MMWRWeekConverter, NNDSSTransformer


class TestMMWRWeekConverter:
    """Tests for MMWR week date conversion."""

    def test_mmwr_week_start_2024_week1(self):
        """Test MMWR week 1 of 2024."""
        converter = MMWRWeekConverter()
        start = converter.get_mmwr_week_start(2024, 1)
        # 2024-01-01 is Monday, so week 1 starts on 2023-12-31 (Sunday)
        assert start.weekday() == 6  # Sunday

    def test_mmwr_week_end_is_saturday(self):
        """Test MMWR week end is always Saturday."""
        converter = MMWRWeekConverter()
        end = converter.get_mmwr_week_end(2024, 1)
        assert end.weekday() == 5  # Saturday

    def test_mmwr_week_range_is_6_days(self):
        """Test week range is 6 days (7 days inclusive)."""
        converter = MMWRWeekConverter()
        start = converter.get_mmwr_week_start(2024, 10)
        end = converter.get_mmwr_week_end(2024, 10)
        assert (end - start).days == 6

    def test_mmwr_consecutive_weeks_7_days_apart(self):
        """Test consecutive weeks start 7 days apart."""
        converter = MMWRWeekConverter()
        week1_start = converter.get_mmwr_week_start(2024, 1)
        week2_start = converter.get_mmwr_week_start(2024, 2)
        assert (week2_start - week1_start).days == 7


class TestNNDSSTransformer:
    """Tests for NNDSS data transformation."""

    def test_load_transforms_to_unified_schema(self, nndss_fixtures_dir: Path):
        """Test transformer produces unified schema output."""
        transformer = NNDSSTransformer(nndss_fixtures_dir)
        df = transformer.load()

        assert not df.empty
        # Check required columns exist
        required = ["disease_name", "disease_slug", "state", "count", "data_source"]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_data_source_is_nndss(self, nndss_fixtures_dir: Path):
        """Test all records have data_source='nndss'."""
        transformer = NNDSSTransformer(nndss_fixtures_dir)
        df = transformer.load()
        assert (df["data_source"] == "nndss").all()

    def test_geo_unit_is_state_only(self, nndss_fixtures_dir: Path):
        """Test only state-level records are included (regions/national filtered)."""
        transformer = NNDSSTransformer(nndss_fixtures_dir)
        df = transformer.load()

        geo_units = df["geo_unit"].unique()
        # Only state records should remain after filtering
        assert list(geo_units) == ["state"]
        # Verify regional/national records were filtered out
        assert "region" not in geo_units
        assert "national" not in geo_units

    def test_state_code_conversion(self, nndss_fixtures_dir: Path):
        """Test state names are converted to codes."""
        transformer = NNDSSTransformer(nndss_fixtures_dir)
        df = transformer.load()

        # Massachusetts should be converted to MA
        state_records = df[df["geo_unit"] == "state"]
        states = state_records["state"].unique()
        # Check for 2-letter codes
        assert any(len(s) == 2 for s in states if pd.notna(s))

    def test_null_counts_filtered(self, nndss_fixtures_dir: Path):
        """Test records with null counts are filtered out."""
        transformer = NNDSSTransformer(nndss_fixtures_dir)
        df = transformer.load()
        assert df["count"].notna().all()

    def test_date_columns_present(self, nndss_fixtures_dir: Path):
        """Test date columns are parsed."""
        transformer = NNDSSTransformer(nndss_fixtures_dir)
        df = transformer.load()

        assert "report_period_start" in df.columns
        assert "report_period_end" in df.columns
        assert df["report_period_start"].notna().all()
        assert df["report_period_end"].notna().all()

    def test_date_range_is_valid(self, nndss_fixtures_dir: Path):
        """Test date range is 6 days (7 days inclusive)."""
        transformer = NNDSSTransformer(nndss_fixtures_dir)
        df = transformer.load()

        date_ranges = (df["report_period_end"] - df["report_period_start"]).dt.days
        assert (date_ranges == 6).all()

    def test_time_unit_is_week(self, nndss_fixtures_dir: Path):
        """Test time_unit is 'week' for all NNDSS records."""
        transformer = NNDSSTransformer(nndss_fixtures_dir)
        df = transformer.load()
        assert (df["time_unit"] == "week").all()

    def test_date_type_is_mmwr(self, nndss_fixtures_dir: Path):
        """Test date_type is 'mmwr' for all NNDSS records."""
        transformer = NNDSSTransformer(nndss_fixtures_dir)
        df = transformer.load()
        assert (df["date_type"] == "mmwr").all()

    def test_original_disease_name_preserved(self, nndss_fixtures_dir: Path):
        """Test original disease name is preserved."""
        transformer = NNDSSTransformer(nndss_fixtures_dir)
        df = transformer.load()
        assert "original_disease_name" in df.columns
        assert df["original_disease_name"].notna().all()

    def test_disease_slug_generated(self, nndss_fixtures_dir: Path):
        """Test disease slugs are generated from disease names."""
        transformer = NNDSSTransformer(nndss_fixtures_dir)
        df = transformer.load()
        assert "disease_slug" in df.columns
        assert df["disease_slug"].notna().all()
        # Slugs should be URL-safe (lowercase, hyphenated)
        for slug in df["disease_slug"].unique():
            assert slug == slug.lower()
            assert " " not in slug

    def test_disease_subtype_column_present(self, nndss_fixtures_dir: Path):
        """Test disease_subtype column is present in output."""
        transformer = NNDSSTransformer(nndss_fixtures_dir)
        df = transformer.load()
        assert "disease_subtype" in df.columns

    def test_measles_aggregation(self, nndss_fixtures_dir: Path):
        """Test Measles, Imported and Measles, Indigenous aggregate to Measles."""
        transformer = NNDSSTransformer(nndss_fixtures_dir)
        df = transformer.load()

        # Disease names now use tracker canonical form (lowercase slug)
        measles_records = df[df["disease_name"] == "measles"]
        assert len(measles_records) > 0

        # Original names should include the variants
        original_names = measles_records["original_disease_name"].unique()
        assert any("Imported" in str(n) for n in original_names)
        assert any("Indigenous" in str(n) for n in original_names)

        # Measles should have no subtype (imported/indigenous are aggregated)
        assert measles_records["disease_subtype"].isna().all()

    def test_meningococcal_subtype_extraction(self, nndss_fixtures_dir: Path):
        """Test Meningococcal serogroups are extracted to disease_subtype."""
        transformer = NNDSSTransformer(nndss_fixtures_dir)
        df = transformer.load()

        # Disease names now use tracker canonical form
        mening_records = df[df["disease_name"] == "meningococcus"]
        assert len(mening_records) > 0

        # Check subtypes are extracted (after stripping "Serogroup " prefix)
        subtypes = mening_records["disease_subtype"].dropna().unique()
        assert "B" in subtypes
        assert "ACWY" in subtypes

    def test_meningococcal_all_serogroups_no_subtype(self, nndss_fixtures_dir: Path):
        """Test Meningococcal All serogroups records have no subtype."""
        transformer = NNDSSTransformer(nndss_fixtures_dir)
        df = transformer.load()

        # Records from "All serogroups" should have null subtype
        all_serogroups = df[df["original_disease_name"].str.contains("All serogroups", na=False)]
        if len(all_serogroups) > 0:
            assert all_serogroups["disease_subtype"].isna().all()
