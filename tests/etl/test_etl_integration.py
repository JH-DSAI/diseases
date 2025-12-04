"""ETL integration tests: CSV -> Transformer -> DuckDB -> Query."""

from app.database import DiseaseDatabase


class TestETLToDuckDBIntegration:
    """End-to-end tests: CSV fixtures -> ETL transformers -> DuckDB -> Query."""

    def test_database_initialized_after_load(self, etl_test_db: DiseaseDatabase):
        """Verify database is initialized after ETL load."""
        assert etl_test_db.is_initialized()

    def test_tracker_diseases_queryable(self, etl_test_db: DiseaseDatabase):
        """Verify tracker diseases can be queried."""
        diseases = etl_test_db.get_diseases(data_source="tracker")
        assert len(diseases) > 0
        # Check for expected diseases from fixtures
        disease_names_lower = [d.lower() for d in diseases]
        assert "measles" in disease_names_lower or any("measles" in d for d in disease_names_lower)

    def test_nndss_diseases_queryable(self, etl_test_db: DiseaseDatabase):
        """Verify NNDSS diseases can be queried."""
        diseases = etl_test_db.get_diseases(data_source="nndss")
        assert len(diseases) > 0

    def test_combined_diseases_from_both_sources(self, etl_test_db: DiseaseDatabase):
        """Verify diseases from both sources are available."""
        all_diseases = etl_test_db.get_diseases()
        tracker_diseases = etl_test_db.get_diseases(data_source="tracker")
        nndss_diseases = etl_test_db.get_diseases(data_source="nndss")

        # Combined should include diseases from both
        assert len(all_diseases) >= max(len(tracker_diseases), len(nndss_diseases))

    def test_get_diseases_with_slugs(self, etl_test_db: DiseaseDatabase):
        """Verify disease slugs are available."""
        diseases = etl_test_db.get_diseases_with_slugs()
        assert len(diseases) > 0

        # Each entry should have name and slug
        for disease in diseases:
            assert "name" in disease
            assert "slug" in disease
            assert disease["slug"] is not None

    def test_disease_slug_lookup_works(self, etl_test_db: DiseaseDatabase):
        """Verify slug -> name lookup after ETL."""
        # First get a valid slug
        diseases = etl_test_db.get_diseases_with_slugs()
        assert len(diseases) > 0

        slug = diseases[0]["slug"]
        expected_name = diseases[0]["name"]

        # Look up by slug
        name = etl_test_db.get_disease_name_by_slug(slug)
        assert name is not None
        assert name == expected_name

    def test_get_states_from_data(self, etl_test_db: DiseaseDatabase):
        """Verify states can be queried."""
        states = etl_test_db.get_states()
        assert len(states) > 0
        # Check for expected states from fixtures
        assert any(s in states for s in ["ID", "CA", "NY", "MA"])

    def test_summary_stats_include_counts(self, etl_test_db: DiseaseDatabase):
        """Verify summary statistics are computed."""
        stats = etl_test_db.get_summary_stats()

        assert "total_states" in stats
        assert "total_cases" in stats
        assert stats["total_states"] > 0
        assert stats["total_cases"] > 0

    def test_summary_stats_include_date_range(self, etl_test_db: DiseaseDatabase):
        """Verify date range is included in stats."""
        stats = etl_test_db.get_summary_stats()

        assert "earliest_date" in stats
        assert "latest_date" in stats
        assert stats["earliest_date"] is not None
        assert stats["latest_date"] is not None

    def test_national_timeseries_query(self, etl_test_db: DiseaseDatabase):
        """Verify national time series query works."""
        # Get a valid disease name
        diseases = etl_test_db.get_diseases()
        assert len(diseases) > 0

        disease_name = diseases[0]
        data = etl_test_db.get_national_disease_timeseries(disease_name, "month")

        assert isinstance(data, list)
        # May be empty if no matching data, but should not error

    def test_state_timeseries_query(self, etl_test_db: DiseaseDatabase):
        """Verify state-level time series query works."""
        diseases = etl_test_db.get_diseases()
        assert len(diseases) > 0

        disease_name = diseases[0]
        data = etl_test_db.get_disease_timeseries_by_state(disease_name, "month")

        assert "states" in data
        assert "national" in data
        assert isinstance(data["states"], dict)

    def test_disease_stats_query(self, etl_test_db: DiseaseDatabase):
        """Verify disease stats query works."""
        diseases = etl_test_db.get_diseases()
        assert len(diseases) > 0

        disease_name = diseases[0]
        stats = etl_test_db.get_disease_stats(disease_name)

        assert "total_cases" in stats
        assert "affected_states" in stats

    def test_age_group_distribution_from_tracker(self, etl_test_db: DiseaseDatabase):
        """Verify age group distribution (from tracker data)."""
        # Tracker data has age groups, NNDSS doesn't
        tracker_diseases = etl_test_db.get_diseases(data_source="tracker")

        if tracker_diseases:
            disease_name = tracker_diseases[0]
            data = etl_test_db.get_age_group_distribution_by_state(disease_name)

            assert "age_groups" in data
            assert "states" in data

    def test_raw_record_count(self, etl_test_db: DiseaseDatabase):
        """Verify raw record count in database."""
        count = etl_test_db.conn.execute("SELECT COUNT(*) FROM disease_data").fetchone()[0]
        assert count > 0

    def test_data_sources_in_database(self, etl_test_db: DiseaseDatabase):
        """Verify both data sources are present in database."""
        sources = etl_test_db.conn.execute(
            "SELECT DISTINCT data_source FROM disease_data ORDER BY data_source"
        ).fetchall()
        source_names = [s[0] for s in sources]

        # Both sources should be loaded
        assert "tracker" in source_names
        assert "nndss" in source_names


class TestETLDataIntegrity:
    """Tests for data integrity after ETL processing."""

    def test_no_null_required_fields(self, etl_test_db: DiseaseDatabase):
        """Verify required fields are not null."""
        required_fields = [
            "disease_name",
            "disease_slug",
            "state",
            "report_period_start",
            "report_period_end",
        ]

        for field in required_fields:
            null_count = etl_test_db.conn.execute(
                f"SELECT COUNT(*) FROM disease_data WHERE {field} IS NULL"
            ).fetchone()[0]
            assert null_count == 0, f"Found {null_count} null values in {field}"

    def test_date_ordering_valid(self, etl_test_db: DiseaseDatabase):
        """Verify end dates are after start dates."""
        invalid_count = etl_test_db.conn.execute("""
            SELECT COUNT(*)
            FROM disease_data
            WHERE report_period_end < report_period_start
        """).fetchone()[0]
        assert invalid_count == 0, "Found records with end date before start date"

    def test_counts_are_non_negative(self, etl_test_db: DiseaseDatabase):
        """Verify case counts are non-negative."""
        negative_count = etl_test_db.conn.execute("""
            SELECT COUNT(*)
            FROM disease_data
            WHERE count < 0
        """).fetchone()[0]
        assert negative_count == 0, "Found records with negative counts"

    def test_disease_slugs_are_lowercase(self, etl_test_db: DiseaseDatabase):
        """Verify disease slugs are lowercase."""
        uppercase_count = etl_test_db.conn.execute("""
            SELECT COUNT(*)
            FROM disease_data
            WHERE disease_slug != LOWER(disease_slug)
        """).fetchone()[0]
        assert uppercase_count == 0, "Found slugs with uppercase characters"

    def test_disease_slugs_no_spaces(self, etl_test_db: DiseaseDatabase):
        """Verify disease slugs have no spaces."""
        space_count = etl_test_db.conn.execute("""
            SELECT COUNT(*)
            FROM disease_data
            WHERE disease_slug LIKE '% %'
        """).fetchone()[0]
        assert space_count == 0, "Found slugs with spaces"
