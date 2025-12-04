"""Tests for database edge cases."""

from app.database import DiseaseDatabase


class TestUninitializedDatabase:
    """Tests for database methods when not initialized."""

    def test_get_diseases_returns_empty(self):
        """Test get_diseases returns empty list when not initialized."""
        db = DiseaseDatabase()
        assert db.get_diseases() == []

    def test_get_diseases_with_source_returns_empty(self):
        """Test get_diseases with data_source returns empty when not initialized."""
        db = DiseaseDatabase()
        assert db.get_diseases(data_source="tracker") == []

    def test_get_diseases_with_slugs_returns_empty(self):
        """Test get_diseases_with_slugs returns empty when not initialized."""
        db = DiseaseDatabase()
        assert db.get_diseases_with_slugs() == []

    def test_get_disease_name_by_slug_returns_none(self):
        """Test get_disease_name_by_slug returns None when not initialized."""
        db = DiseaseDatabase()
        assert db.get_disease_name_by_slug("measles") is None

    def test_get_states_returns_empty(self):
        """Test get_states returns empty list when not initialized."""
        db = DiseaseDatabase()
        assert db.get_states() == []

    def test_get_summary_stats_returns_empty(self):
        """Test get_summary_stats returns empty dict when not initialized."""
        db = DiseaseDatabase()
        assert db.get_summary_stats() == {}

    def test_get_disease_totals_returns_empty(self):
        """Test get_disease_totals returns empty list when not initialized."""
        db = DiseaseDatabase()
        assert db.get_disease_totals() == []

    def test_get_national_timeseries_returns_empty(self):
        """Test get_national_disease_timeseries returns empty when not initialized."""
        db = DiseaseDatabase()
        assert db.get_national_disease_timeseries("Measles") == []

    def test_get_disease_stats_returns_empty(self):
        """Test get_disease_stats returns empty dict when not initialized."""
        db = DiseaseDatabase()
        assert db.get_disease_stats("Measles") == {}

    def test_get_age_group_distribution_returns_empty(self):
        """Test get_age_group_distribution_by_state returns empty when not initialized."""
        db = DiseaseDatabase()
        result = db.get_age_group_distribution_by_state("Measles")
        assert result == {"states": {}, "age_groups": [], "available_states": []}

    def test_get_timeseries_by_state_returns_empty(self):
        """Test get_disease_timeseries_by_state returns empty when not initialized."""
        db = DiseaseDatabase()
        result = db.get_disease_timeseries_by_state("Measles")
        assert result == {"states": {}, "national": [], "available_states": []}

    def test_is_initialized_false(self):
        """Test is_initialized returns False for new database."""
        db = DiseaseDatabase()
        assert db.is_initialized() is False


class TestDataSourceFilters:
    """Tests for data_source filter branches using the session-scoped test db."""

    def test_get_diseases_with_tracker_source(self, etl_test_db):
        """Test get_diseases filters by tracker source."""
        diseases = etl_test_db.get_diseases(data_source="tracker")
        assert isinstance(diseases, list)

    def test_get_diseases_with_nndss_source(self, etl_test_db):
        """Test get_diseases filters by nndss source."""
        diseases = etl_test_db.get_diseases(data_source="nndss")
        assert isinstance(diseases, list)

    def test_get_diseases_with_slugs_tracker_source(self, etl_test_db):
        """Test get_diseases_with_slugs filters by tracker source."""
        diseases = etl_test_db.get_diseases_with_slugs(data_source="tracker")
        assert isinstance(diseases, list)

    def test_get_states_with_source(self, etl_test_db):
        """Test get_states filters by data source."""
        states = etl_test_db.get_states(data_source="tracker")
        assert isinstance(states, list)

    def test_get_summary_stats_with_source(self, etl_test_db):
        """Test get_summary_stats filters by data source."""
        stats = etl_test_db.get_summary_stats(data_source="tracker")
        assert isinstance(stats, dict)

    def test_get_disease_totals_with_source(self, etl_test_db):
        """Test get_disease_totals filters by data source."""
        totals = etl_test_db.get_disease_totals(data_source="tracker")
        assert isinstance(totals, list)

    def test_get_national_timeseries_with_source(self, etl_test_db):
        """Test get_national_disease_timeseries filters by data source."""
        data = etl_test_db.get_national_disease_timeseries("Measles", data_source="tracker")
        assert isinstance(data, list)

    def test_get_disease_stats_with_source(self, etl_test_db):
        """Test get_disease_stats filters by data source."""
        stats = etl_test_db.get_disease_stats("Measles", data_source="tracker")
        assert isinstance(stats, dict)

    def test_get_age_distribution_with_source(self, etl_test_db):
        """Test get_age_group_distribution_by_state filters by data source."""
        data = etl_test_db.get_age_group_distribution_by_state("Measles", data_source="tracker")
        assert isinstance(data, dict)

    def test_get_timeseries_by_state_with_source(self, etl_test_db):
        """Test get_disease_timeseries_by_state filters by data source."""
        data = etl_test_db.get_disease_timeseries_by_state("Measles", data_source="tracker")
        assert isinstance(data, dict)
