"""Tests for NNDSS data loading and transformation"""

from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from app.nndss_loader import MMWRWeekConverter, NNDSSTransformer, load_nndss_data


class TestMMWRWeekConverter:
    """Tests for MMWR week date conversion"""

    def test_mmwr_week_start_2022_week1(self):
        """Test MMWR week 1 of 2022 (Jan 1 is Saturday)"""
        converter = MMWRWeekConverter()
        start = converter.get_mmwr_week_start(2022, 1)
        assert start == datetime(2022, 1, 2)  # Sunday, Jan 2

    def test_mmwr_week_end_2022_week1(self):
        """Test MMWR week 1 end date"""
        converter = MMWRWeekConverter()
        end = converter.get_mmwr_week_end(2022, 1)
        assert end == datetime(2022, 1, 8)  # Saturday, Jan 8

    def test_mmwr_week_range(self):
        """Test week range is 7 days"""
        converter = MMWRWeekConverter()
        start = converter.get_mmwr_week_start(2022, 10)
        end = converter.get_mmwr_week_end(2022, 10)
        assert (end - start).days == 6  # 7 days inclusive

    def test_mmwr_multiple_weeks(self):
        """Test multiple consecutive weeks"""
        converter = MMWRWeekConverter()
        week1_start = converter.get_mmwr_week_start(2022, 1)
        week2_start = converter.get_mmwr_week_start(2022, 2)
        assert (week2_start - week1_start).days == 7


class TestNNDSSTransformer:
    """Tests for NNDSS data transformation"""

    @pytest.fixture
    def sample_nndss_csv(self, tmp_path):
        """Create a sample NNDSS CSV for testing"""
        csv_path = tmp_path / "test_nndss.csv"
        sample_data = """Reporting Area,Current MMWR Year,MMWR WEEK,Label,Current week,Current week, flag,Previous 52 week Max,Previous 52 weeks Max, flag,Cumulative YTD Current MMWR Year,Cumulative YTD Current MMWR Year, flag,Cumulative YTD Previous MMWR Year,Cumulative YTD Previous MMWR Year, flag,LOCATION1,LOCATION2,sort_order,geocode
US RESIDENTS,2022,1,Anthrax,0,-,0,-,0,-,0,-,,,20220100001,
MASSACHUSETTS,2022,1,Pertussis,5,-,10,-,5,-,100,-,MASSACHUSETTS,,20220100005,"POINT (-71.481104 42.151077)"
NEW YORK,2022,1,Measles,2,-,5,-,2,-,50,-,NEW YORK,,20220100011,"POINT (-75.59655 42.921241)"
NEW ENGLAND,2022,1,Pertussis,15,-,30,-,15,-,200,-,,NEW ENGLAND,20220100002,
"""
        csv_path.write_text(sample_data)
        return csv_path

    def test_load_sample_csv(self, sample_nndss_csv):
        """Test loading a sample NNDSS CSV"""
        transformer = NNDSSTransformer(sample_nndss_csv)
        df = transformer.load_and_transform()

        # Check basic structure
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "data_source" in df.columns
        assert "disease_name" in df.columns
        assert all(df["data_source"] == "nndss")

    def test_geo_unit_classification(self, sample_nndss_csv):
        """Test geographic unit classification"""
        transformer = NNDSSTransformer(sample_nndss_csv)
        df = transformer.load_and_transform()

        # Check classification
        national = df[df["Reporting Area"] == "US RESIDENTS"]
        if len(national) > 0:
            assert national.iloc[0]["geo_unit"] == "national"

        regional = df[df["Reporting Area"] == "NEW ENGLAND"]
        if len(regional) > 0:
            assert regional.iloc[0]["geo_unit"] == "region"

        state = df[df["Reporting Area"] == "MASSACHUSETTS"]
        if len(state) > 0:
            assert state.iloc[0]["geo_unit"] == "state"

    def test_date_parsing(self, sample_nndss_csv):
        """Test MMWR week to date conversion"""
        transformer = NNDSSTransformer(sample_nndss_csv)
        df = transformer.load_and_transform()

        # Check dates were parsed
        assert df["report_period_start"].notna().all()
        assert df["report_period_end"].notna().all()

        # Check date range is 7 days
        date_ranges = (df["report_period_end"] - df["report_period_start"]).dt.days
        assert all(date_ranges == 6)  # 7 days inclusive (0-6)

    def test_state_code_conversion(self, sample_nndss_csv):
        """Test state name to code conversion"""
        transformer = NNDSSTransformer(sample_nndss_csv)
        df = transformer.load_and_transform()

        ma_records = df[df["Reporting Area"] == "MASSACHUSETTS"]
        if len(ma_records) > 0:
            assert ma_records.iloc[0]["state"] == "MA"

        ny_records = df[df["Reporting Area"] == "NEW YORK"]
        if len(ny_records) > 0:
            assert ny_records.iloc[0]["state"] == "NY"

    def test_count_cleaning(self, sample_nndss_csv):
        """Test case count cleaning and conversion"""
        transformer = NNDSSTransformer(sample_nndss_csv)
        df = transformer.load_and_transform()

        # All counts should be integer or NaN
        assert df["count"].dtype in ["Int64", "int64", "float64"]

        # Verify some expected counts
        pertussis_ma = df[(df["disease_name"] == "Pertussis") & (df["state"] == "MA")]
        if len(pertussis_ma) > 0:
            assert pertussis_ma.iloc[0]["count"] == 5

    def test_null_counts_filtered(self, sample_nndss_csv):
        """Test that records with NULL counts are filtered out"""
        transformer = NNDSSTransformer(sample_nndss_csv)
        df = transformer.load_and_transform()

        # No NULL counts should remain
        assert df["count"].notna().all()

    def test_unified_schema_columns(self, sample_nndss_csv):
        """Test all required unified schema columns are present"""
        transformer = NNDSSTransformer(sample_nndss_csv)
        df = transformer.load_and_transform()

        required_columns = [
            "report_period_start",
            "report_period_end",
            "date_type",
            "time_unit",
            "disease_name",
            "disease_subtype",
            "state",
            "reporting_jurisdiction",
            "geo_name",
            "geo_unit",
            "age_group",
            "confirmation_status",
            "outcome",
            "count",
            "data_source",
            "original_disease_name",
        ]

        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"

    def test_metadata_fields(self, sample_nndss_csv):
        """Test metadata fields are set correctly"""
        transformer = NNDSSTransformer(sample_nndss_csv)
        df = transformer.load_and_transform()

        # Check data source
        assert all(df["data_source"] == "nndss")

        # Check date type
        assert all(df["date_type"] == "mmwr")

        # Check time unit
        assert all(df["time_unit"] == "week")

        # Check outcome
        assert all(df["outcome"] == "cases")

        # Check NULL fields (not in NNDSS)
        assert df["age_group"].isna().all()
        assert df["confirmation_status"].isna().all()


@pytest.mark.skipif(
    not Path("nndss_data/NNDSS_Weekly_Data_20251121.csv").exists(),
    reason="Full NNDSS CSV not available"
)
class TestFullNNDSSLoad:
    """Integration tests with full NNDSS CSV (skipped if file not present)"""

    def test_load_full_nndss_csv(self):
        """Test loading the full NNDSS CSV"""
        nndss_file = Path("nndss_data/NNDSS_Weekly_Data_20251121.csv")
        df = load_nndss_data(nndss_file)

        # Basic checks
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 100000  # Should have many records
        assert all(df["data_source"] == "nndss")

        # Check for expected diseases
        diseases = df["disease_name"].unique()
        assert "Pertussis" in diseases
        assert "Measles" in diseases

        # Check geographic diversity
        states = df[df["geo_unit"] == "state"]["state"].unique()
        assert len(states) > 40  # Should have most states

        print(f"Loaded {len(df)} records")
        print(f"Unique diseases: {len(diseases)}")
        print(f"States with data: {len(states)}")

    def test_full_csv_data_quality(self):
        """Test data quality of full NNDSS CSV"""
        nndss_file = Path("nndss_data/NNDSS_Weekly_Data_20251121.csv")
        df = load_nndss_data(nndss_file)

        # No NULL counts
        assert df["count"].notna().all()

        # All counts are non-negative
        assert (df["count"] >= 0).all()

        # Dates are valid
        assert df["report_period_start"].notna().all()
        assert df["report_period_end"].notna().all()
        assert (df["report_period_end"] >= df["report_period_start"]).all()

        # Consistent metadata
        assert all(df["data_source"] == "nndss")
        assert all(df["date_type"] == "mmwr")
        assert all(df["time_unit"] == "week")
