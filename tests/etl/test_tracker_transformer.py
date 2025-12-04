"""Tests for state disease tracker data transformation."""

from pathlib import Path

from app.etl.transformers.tracker import TrackerTransformer


class TestTrackerTransformer:
    """Tests for tracker data transformation."""

    def test_load_transforms_to_unified_schema(self, fixtures_dir: Path):
        """Test transformer produces unified schema output."""
        transformer = TrackerTransformer(fixtures_dir)
        df = transformer.load()

        assert not df.empty
        required = ["disease_name", "disease_slug", "state", "count", "data_source"]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_data_source_is_tracker(self, fixtures_dir: Path):
        """Test all records have data_source='tracker'."""
        transformer = TrackerTransformer(fixtures_dir)
        df = transformer.load()
        assert (df["data_source"] == "tracker").all()

    def test_loads_multiple_states(self, fixtures_dir: Path):
        """Test transformer loads data from multiple state directories."""
        transformer = TrackerTransformer(fixtures_dir)
        df = transformer.load()

        states = df["state"].unique()
        assert len(states) >= 2, "Should load data from multiple states"

    def test_original_disease_name_preserved(self, fixtures_dir: Path):
        """Test original disease name is preserved before normalization."""
        transformer = TrackerTransformer(fixtures_dir)
        df = transformer.load()

        assert "original_disease_name" in df.columns
        assert df["original_disease_name"].notna().all()

    def test_disease_slug_generated(self, fixtures_dir: Path):
        """Test disease slugs are generated."""
        transformer = TrackerTransformer(fixtures_dir)
        df = transformer.load()

        assert "disease_slug" in df.columns
        assert df["disease_slug"].notna().all()

    def test_date_columns_present(self, fixtures_dir: Path):
        """Test date columns are parsed from CSV."""
        transformer = TrackerTransformer(fixtures_dir)
        df = transformer.load()

        assert "report_period_start" in df.columns
        assert "report_period_end" in df.columns
        assert df["report_period_start"].notna().all()
        assert df["report_period_end"].notna().all()

    def test_age_group_present(self, fixtures_dir: Path):
        """Test age_group column is present (tracker data has age groups)."""
        transformer = TrackerTransformer(fixtures_dir)
        df = transformer.load()

        assert "age_group" in df.columns
        # Tracker fixtures should have age group data
        assert df["age_group"].notna().any()

    def test_geo_unit_is_state(self, fixtures_dir: Path):
        """Test geo_unit is 'state' for tracker data."""
        transformer = TrackerTransformer(fixtures_dir)
        df = transformer.load()

        assert (df["geo_unit"] == "state").all()

    def test_selects_latest_file_per_state(self, tmp_path: Path):
        """Test transformer selects only the latest file per state."""
        # Create structure with multiple files per state
        data_dir = tmp_path / "data" / "states" / "ID"
        data_dir.mkdir(parents=True)

        csv_content_old = """report_period_start,report_period_end,date_type,time_unit,disease_name,disease_subtype,state,reporting_jurisdiction,geo_name,geo_unit,age_group,confirmation_status,outcome,count
2025-08-03,2025-08-09,cccd,week,measles,NA,ID,ID,ID,state,1-4 y,confirmed,cases,5"""

        csv_content_new = """report_period_start,report_period_end,date_type,time_unit,disease_name,disease_subtype,state,reporting_jurisdiction,geo_name,geo_unit,age_group,confirmation_status,outcome,count
2025-08-03,2025-08-09,cccd,week,measles,NA,ID,ID,ID,state,1-4 y,confirmed,cases,10"""

        # Create older file with count=5
        (data_dir / "20251101-old.csv").write_text(csv_content_old)
        # Create newer file with count=10
        (data_dir / "20251107-new.csv").write_text(csv_content_new)

        transformer = TrackerTransformer(tmp_path)
        df = transformer.load()

        # Should have loaded only from the newer file
        assert len(df) == 1
        assert df.iloc[0]["count"] == 10

    def test_empty_directory_returns_empty_dataframe(self, tmp_path: Path):
        """Test transformer handles missing data directory gracefully."""
        transformer = TrackerTransformer(tmp_path / "nonexistent")
        df = transformer.load()
        assert df.empty
