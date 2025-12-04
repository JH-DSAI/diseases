"""DuckDB database connection and data loading.

This module manages the DuckDB database connection and provides query
interfaces for disease data. Data loading is delegated to the ETL
transformers for each data source.
"""

import logging
import threading

import duckdb

from app.config import settings
from app.etl.config import get_transformer, list_sources
from app.etl.normalizers.disease_names import TRACKER_TO_NNDSS

logger = logging.getLogger(__name__)


class DiseaseDatabase:
    """Manages DuckDB connection and disease data queries."""

    def __init__(self):
        self.conn: duckdb.DuckDBPyConnection | None = None
        self._initialized = False
        self._lock = threading.RLock()

    def connect(self) -> duckdb.DuckDBPyConnection:
        """Establish DuckDB connection."""
        if self.conn is None:
            self.conn = duckdb.connect(settings.database_path)
            logger.info(f"Connected to DuckDB: {settings.database_path}")
        return self.conn

    def load_all_sources(self) -> None:
        """Load data from all configured sources."""
        if self._initialized:
            logger.info("Database already initialized")
            return

        conn = self.connect()

        # Create table with explicit schema to avoid type inference issues
        conn.execute("DROP TABLE IF EXISTS disease_data")
        conn.execute("""
            CREATE TABLE disease_data (
                report_period_start TIMESTAMP,
                report_period_end TIMESTAMP,
                date_type VARCHAR,
                time_unit VARCHAR,
                disease_name VARCHAR,
                disease_slug VARCHAR,
                disease_subtype VARCHAR,
                reporting_jurisdiction VARCHAR,
                state VARCHAR,
                geo_name VARCHAR,
                geo_unit VARCHAR,
                age_group VARCHAR,
                confirmation_status VARCHAR,
                outcome VARCHAR,
                count BIGINT,
                data_source VARCHAR,
                original_disease_name VARCHAR
            )
        """)

        # Load each data source
        for source_name in list_sources():
            self._load_source(source_name)

        # Create indexes after all data is loaded
        self._create_indexes()

        # Create disease name mapping table for reference
        self._create_disease_mapping_table()

        self._initialized = True

        # Log summary
        total_count = conn.execute("SELECT COUNT(*) FROM disease_data").fetchone()[0]
        logger.info(f"Database initialized with {total_count} total records")

    def _load_source(self, source_name: str) -> None:
        """
        Load data from a specific source using its transformer.

        Args:
            source_name: Name of the data source to load
        """
        conn = self.connect()

        # Get source path based on source name
        if source_name == "tracker":
            source_path = settings.data_directory
        elif source_name == "nndss":
            source_path = settings.nndss_data_directory
        else:
            logger.warning(f"Unknown source path for: {source_name}")
            return

        if not source_path.exists():
            logger.warning(f"Source path not found for {source_name}: {source_path}")
            return

        try:
            # Get transformer and load data
            transformer_cls = get_transformer(source_name)
            transformer = transformer_cls(source_path)
            df = transformer.load()

            if df.empty:
                logger.warning(f"No data loaded from {source_name}")
                return

            # Insert into database
            conn.register("temp_data", df)
            conn.execute("""
                INSERT INTO disease_data
                SELECT * FROM temp_data
            """)
            conn.unregister("temp_data")

            logger.info(f"Loaded {len(df)} rows from {source_name}")

        except Exception as e:
            logger.error(f"Error loading {source_name}: {e}", exc_info=True)

    def _create_indexes(self) -> None:
        """Create indexes for common queries."""
        conn = self.connect()
        conn.execute("CREATE INDEX IF NOT EXISTS idx_disease_name ON disease_data(disease_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_disease_slug ON disease_data(disease_slug)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_state ON disease_data(state)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_report_period ON disease_data(report_period_start)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_data_source ON disease_data(data_source)")
        logger.info("Created database indexes")

    def _create_disease_mapping_table(self) -> None:
        """Create and populate the disease name mapping table for reference."""
        conn = self.connect()

        conn.execute("DROP TABLE IF EXISTS disease_name_mapping")
        conn.execute("""
            CREATE TABLE disease_name_mapping (
                tracker_name VARCHAR,
                nndss_name VARCHAR,
                PRIMARY KEY (tracker_name)
            )
        """)

        for tracker_name, nndss_name in TRACKER_TO_NNDSS.items():
            conn.execute(
                "INSERT INTO disease_name_mapping (tracker_name, nndss_name) VALUES (?, ?)",
                [tracker_name, nndss_name],
            )

        mapping_count = conn.execute("SELECT COUNT(*) FROM disease_name_mapping").fetchone()[0]
        logger.info(f"Created disease_name_mapping table with {mapping_count} mappings")

    def is_initialized(self) -> bool:
        """Check if database has been initialized with data."""
        return self._initialized

    # Query methods

    def get_diseases(self, data_source: str | None = None) -> list[str]:
        """Get list of unique diseases in the database."""
        if not self._initialized:
            return []

        with self._lock:
            if data_source:
                result = self.conn.execute(
                    """
                    SELECT DISTINCT disease_name
                    FROM disease_data
                    WHERE data_source = ?
                    ORDER BY disease_name
                """,
                    [data_source],
                ).fetchall()
            else:
                result = self.conn.execute("""
                    SELECT DISTINCT disease_name
                    FROM disease_data
                    ORDER BY disease_name
                """).fetchall()

            return [row[0] for row in result]

    def get_diseases_with_slugs(self, data_source: str | None = None) -> list[dict]:
        """Get list of unique diseases with their slugs."""
        if not self._initialized:
            return []

        with self._lock:
            if data_source:
                result = self.conn.execute(
                    """
                    SELECT DISTINCT disease_name, disease_slug
                    FROM disease_data
                    WHERE data_source = ?
                    ORDER BY disease_name
                """,
                    [data_source],
                ).fetchall()
            else:
                result = self.conn.execute("""
                    SELECT DISTINCT disease_name, disease_slug
                    FROM disease_data
                    ORDER BY disease_name
                """).fetchall()

            return [{"name": row[0], "slug": row[1]} for row in result]

    def get_disease_name_by_slug(self, slug: str) -> str | None:
        """Look up disease name by its slug."""
        if not self._initialized:
            return None

        with self._lock:
            result = self.conn.execute(
                """
                SELECT DISTINCT disease_name
                FROM disease_data
                WHERE disease_slug = ?
                LIMIT 1
            """,
                [slug],
            ).fetchone()

            return result[0] if result else None

    def get_states(self, data_source: str | None = None) -> list[str]:
        """Get list of unique states in the database."""
        if not self._initialized:
            return []

        with self._lock:
            if data_source:
                result = self.conn.execute(
                    """
                    SELECT DISTINCT state
                    FROM disease_data
                    WHERE data_source = ?
                    ORDER BY state
                """,
                    [data_source],
                ).fetchall()
            else:
                result = self.conn.execute("""
                    SELECT DISTINCT state
                    FROM disease_data
                    ORDER BY state
                """).fetchall()

            return [row[0] for row in result]

    def get_summary_stats(self, data_source: str | None = None) -> dict:
        """Get summary statistics across all data."""
        if not self._initialized:
            return {}

        with self._lock:
            if data_source:
                stats = self.conn.execute(
                    """
                    SELECT
                        COUNT(*) as total_records,
                        COUNT(DISTINCT disease_name) as total_diseases,
                        COUNT(DISTINCT state) as total_states,
                        SUM(count) as total_cases,
                        MIN(report_period_start) as earliest_date,
                        MAX(report_period_end) as latest_date
                    FROM disease_data
                    WHERE data_source = ?
                """,
                    [data_source],
                ).fetchone()
            else:
                stats = self.conn.execute("""
                    SELECT
                        COUNT(*) as total_records,
                        COUNT(DISTINCT disease_name) as total_diseases,
                        COUNT(DISTINCT state) as total_states,
                        SUM(count) as total_cases,
                        MIN(report_period_start) as earliest_date,
                        MAX(report_period_end) as latest_date
                    FROM disease_data
                """).fetchone()

            if not stats:
                return {}

            source_breakdown = self.conn.execute("""
                SELECT data_source, COUNT(*) as record_count, SUM(count) as case_count
                FROM disease_data
                GROUP BY data_source
            """).fetchall()

            return {
                "total_records": stats[0],
                "total_diseases": stats[1],
                "total_states": stats[2],
                "total_cases": stats[3],
                "earliest_date": stats[4],
                "latest_date": stats[5],
                "disease_totals": self.get_disease_totals(data_source),
                "source_breakdown": {
                    row[0]: {"records": row[1], "cases": row[2]} for row in source_breakdown
                },
            }

    def get_disease_totals(self, data_source: str | None = None) -> list[dict]:
        """Get total case counts for each disease."""
        if not self._initialized:
            return []

        with self._lock:
            if data_source:
                result = self.conn.execute(
                    """
                    SELECT disease_name, SUM(count) as total_cases
                    FROM disease_data
                    WHERE data_source = ?
                    GROUP BY disease_name
                    ORDER BY disease_name
                """,
                    [data_source],
                ).fetchall()
            else:
                result = self.conn.execute("""
                    SELECT disease_name, SUM(count) as total_cases
                    FROM disease_data
                    GROUP BY disease_name
                    ORDER BY disease_name
                """).fetchall()

            return [
                {"disease_name": row[0], "total_cases": int(row[1]) if row[1] else 0}
                for row in result
            ]

    def get_national_disease_timeseries(
        self, disease_name: str, granularity: str = "month", data_source: str | None = None
    ) -> list[dict]:
        """Get time series data for a disease aggregated nationally."""
        if not self._initialized:
            return []

        if granularity not in ["month", "week"]:
            granularity = "month"

        with self._lock:
            if data_source:
                query = f"""
                    SELECT
                        DATE_TRUNC('{granularity}', report_period_start) as period,
                        SUM(count) as total_cases
                    FROM disease_data
                    WHERE disease_name = ? AND data_source = ?
                    GROUP BY DATE_TRUNC('{granularity}', report_period_start)
                    ORDER BY period ASC
                """
                result = self.conn.execute(query, [disease_name, data_source]).fetchall()
            else:
                query = f"""
                    SELECT
                        DATE_TRUNC('{granularity}', report_period_start) as period,
                        SUM(count) as total_cases
                    FROM disease_data
                    WHERE disease_name = ?
                    GROUP BY DATE_TRUNC('{granularity}', report_period_start)
                    ORDER BY period ASC
                """
                result = self.conn.execute(query, [disease_name]).fetchall()

            return [
                {"period": str(row[0]), "total_cases": int(row[1]) if row[1] else 0}
                for row in result
            ]

    def get_disease_stats(self, disease_name: str, data_source: str | None = None) -> dict:
        """Get summary statistics for a specific disease."""
        if not self._initialized:
            return {}

        with self._lock:
            where_clause = (
                "WHERE disease_name = ?"
                if not data_source
                else "WHERE disease_name = ? AND data_source = ?"
            )
            params = [disease_name] if not data_source else [disease_name, data_source]

            total_cases_result = self.conn.execute(
                f"""
                SELECT SUM(count) as total_cases FROM disease_data {where_clause}
            """,
                params,
            ).fetchone()
            total_cases = int(total_cases_result[0]) if total_cases_result[0] else 0

            affected_states_result = self.conn.execute(
                f"""
                SELECT COUNT(DISTINCT state) as affected_states FROM disease_data {where_clause}
            """,
                params,
            ).fetchone()
            affected_states = int(affected_states_result[0]) if affected_states_result[0] else 0

            affected_counties_result = self.conn.execute(
                f"""
                SELECT COUNT(DISTINCT geo_name) as affected_counties
                FROM disease_data
                {where_clause} AND geo_name IS NOT NULL AND geo_name != ''
            """,
                params,
            ).fetchone()
            affected_counties = (
                int(affected_counties_result[0]) if affected_counties_result[0] else 0
            )

            latest_two_week_result = self.conn.execute(
                f"""
                WITH latest_date AS (
                    SELECT MAX(report_period_end) as max_date FROM disease_data {where_clause}
                )
                SELECT SUM(count) as two_week_cases
                FROM disease_data
                {where_clause}
                  AND report_period_end >= (SELECT max_date - INTERVAL 14 DAYS FROM latest_date)
                  AND report_period_end <= (SELECT max_date FROM latest_date)
            """,
                params + params,
            ).fetchone()
            two_week_cases = int(latest_two_week_result[0]) if latest_two_week_result[0] else 0

            return {
                "total_cases": total_cases,
                "affected_states": affected_states,
                "affected_counties": affected_counties,
                "two_week_cases": two_week_cases,
            }

    def get_age_group_distribution_by_state(
        self, disease_name: str, data_source: str | None = None
    ) -> dict:
        """Get age group distribution by state for a disease."""
        if not self._initialized:
            return {"states": {}, "age_groups": [], "available_states": []}

        with self._lock:
            where_clause = (
                "WHERE disease_name = ?"
                if not data_source
                else "WHERE disease_name = ? AND data_source = ?"
            )
            params = [disease_name] if not data_source else [disease_name, data_source]

            states_result = self.conn.execute(
                f"""
                SELECT DISTINCT state FROM disease_data {where_clause} ORDER BY state
            """,
                params,
            ).fetchall()
            available_states = [row[0] for row in states_result]

            age_group_result = self.conn.execute(
                f"""
                SELECT state, age_group, SUM(count) as total_cases
                FROM disease_data
                {where_clause}
                  AND age_group IS NOT NULL AND age_group != ''
                  AND LOWER(age_group) NOT LIKE '%total%'
                GROUP BY state, age_group
                ORDER BY state, age_group
            """,
                params,
            ).fetchall()

            age_groups_result = self.conn.execute(
                f"""
                SELECT DISTINCT age_group FROM disease_data
                {where_clause}
                  AND age_group IS NOT NULL AND age_group != ''
                  AND LOWER(age_group) NOT LIKE '%total%'
                ORDER BY age_group
            """,
                params,
            ).fetchall()
            age_groups = [row[0] for row in age_groups_result]

            states_data = {}
            for state in available_states:
                state_total = 0
                state_age_counts = {}

                for row in age_group_result:
                    if row[0] == state:
                        state_age_counts[row[1]] = int(row[2]) if row[2] else 0
                        state_total += state_age_counts[row[1]]

                state_age_percentages = {}
                for age_group in age_groups:
                    count = state_age_counts.get(age_group, 0)
                    percentage = (count / state_total * 100) if state_total > 0 else 0
                    state_age_percentages[age_group] = {
                        "count": count,
                        "percentage": round(percentage, 2),
                    }

                states_data[state] = state_age_percentages

            return {
                "states": states_data,
                "age_groups": age_groups,
                "available_states": available_states,
            }

    def get_disease_timeseries_by_state(
        self, disease_name: str, granularity: str = "month", data_source: str | None = None
    ) -> dict:
        """Get time series data for a disease broken down by state."""
        if not self._initialized:
            return {"states": {}, "national": [], "available_states": []}

        if granularity not in ["month", "week"]:
            granularity = "month"

        with self._lock:
            where_clause = (
                "WHERE disease_name = ?"
                if not data_source
                else "WHERE disease_name = ? AND data_source = ?"
            )
            params = [disease_name] if not data_source else [disease_name, data_source]

            states_result = self.conn.execute(
                f"""
                SELECT DISTINCT state FROM disease_data {where_clause} ORDER BY state
            """,
                params,
            ).fetchall()
            available_states = [row[0] for row in states_result]

            state_result = self.conn.execute(
                f"""
                SELECT state, DATE_TRUNC('{granularity}', report_period_start) as period, SUM(count) as total_cases
                FROM disease_data
                {where_clause}
                GROUP BY state, DATE_TRUNC('{granularity}', report_period_start)
                ORDER BY state, period ASC
            """,
                params,
            ).fetchall()

            states_data = {}
            for row in state_result:
                state, period, cases = row
                if state not in states_data:
                    states_data[state] = []
                states_data[state].append(
                    {"period": str(period), "cases": int(cases) if cases else 0}
                )

            national_result = self.conn.execute(
                f"""
                SELECT DATE_TRUNC('{granularity}', report_period_start) as period, SUM(count) as total_cases
                FROM disease_data
                {where_clause}
                GROUP BY DATE_TRUNC('{granularity}', report_period_start)
                ORDER BY period ASC
            """,
                params,
            ).fetchall()
            national_data = [
                {"period": str(row[0]), "cases": int(row[1]) if row[1] else 0}
                for row in national_result
            ]

            return {
                "states": states_data,
                "national": national_data,
                "available_states": available_states,
            }

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Closed DuckDB connection")


# Global database instance
db = DiseaseDatabase()
