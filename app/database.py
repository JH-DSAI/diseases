"""DuckDB database connection and data loading"""

import logging
import threading
from pathlib import Path

import duckdb
import pandas as pd

from app.config import settings
from app.disease_mappings import TRACKER_TO_NNDSS
from app.nndss_loader import load_nndss_data

logger = logging.getLogger(__name__)


class DiseaseDatabase:
    """Manages DuckDB connection and disease data loading"""

    def __init__(self):
        self.conn: duckdb.DuckDBPyConnection | None = None
        self._initialized = False
        self._lock = threading.RLock()  # Reentrant lock for thread-safe database access

    def connect(self) -> duckdb.DuckDBPyConnection:
        """Establish DuckDB connection"""
        if self.conn is None:
            self.conn = duckdb.connect(settings.database_path)
            logger.info(f"Connected to DuckDB: {settings.database_path}")
        return self.conn

    def load_csv_files(self) -> None:
        """Load latest CSV file per state from data directory into DuckDB"""
        if self._initialized:
            logger.info("Database already initialized")
            return

        conn = self.connect()
        data_dir = settings.data_directory / "data" / "states"

        if not data_dir.exists():
            logger.warning(f"Data directory not found: {data_dir}")
            return

        # Find all CSV files
        all_csv_files = list(data_dir.rglob("*.csv"))
        logger.info(f"Found {len(all_csv_files)} total CSV files")

        if not all_csv_files:
            logger.warning("No CSV files found to load")
            return

        # Group files by state and select the latest for each
        # File format: YYYYMMDD-HHMMSS_STATE_UPLOADERNAME.csv
        from collections import defaultdict
        files_by_state = defaultdict(list)

        for csv_file in all_csv_files:
            # Extract state from parent directory name
            state = csv_file.parent.name
            files_by_state[state].append(csv_file)

        # Select the latest file for each state (sorted by filename, which includes timestamp)
        csv_files = []
        for state, state_files in files_by_state.items():
            # Sort by filename descending (latest timestamp first)
            latest_file = sorted(state_files, key=lambda f: f.name, reverse=True)[0]
            csv_files.append(latest_file)
            logger.info(f"Selected latest file for {state}: {latest_file.name}")

        logger.info(f"Loading {len(csv_files)} latest files (one per state)")

        # Load each CSV into a temporary list
        all_data = []
        for csv_file in csv_files:
            try:
                # Parse date columns during CSV loading
                df = pd.read_csv(csv_file, parse_dates=['report_period_start', 'report_period_end'])
                logger.info(f"Loaded {csv_file.name}: {len(df)} rows")
                all_data.append(df)
            except Exception as e:
                logger.error(f"Error loading {csv_file}: {e}")

        if not all_data:
            logger.error("No data loaded from CSV files")
            return

        # Combine all DataFrames
        combined_df = pd.concat(all_data, ignore_index=True)

        # Normalize column names (handle both 'reporting_jurisdiction' and 'state' columns)
        if 'reporting_jurisdiction' in combined_df.columns and 'state' not in combined_df.columns:
            combined_df['state'] = combined_df['reporting_jurisdiction']
        elif 'state' in combined_df.columns and 'reporting_jurisdiction' not in combined_df.columns:
            combined_df['reporting_jurisdiction'] = combined_df['state']

        # Store original disease names before mapping
        combined_df['original_disease_name'] = combined_df['disease_name']

        # Apply disease name mapping (tracker → NNDSS standard)
        def map_disease_name(name):
            """Map tracker disease name to NNDSS standard name"""
            if pd.isna(name):
                return name
            name_lower = str(name).lower()
            return TRACKER_TO_NNDSS.get(name_lower, name)

        combined_df['disease_name'] = combined_df['disease_name'].apply(map_disease_name)

        # Add data source column
        combined_df['data_source'] = 'tracker'

        # Ensure consistent column order
        expected_columns = [
            'report_period_start', 'report_period_end', 'date_type', 'time_unit',
            'disease_name', 'disease_subtype', 'reporting_jurisdiction', 'state',
            'geo_name', 'geo_unit', 'age_group', 'confirmation_status', 'outcome', 'count',
            'data_source', 'original_disease_name'
        ]

        # Keep only expected columns that exist
        available_columns = [col for col in expected_columns if col in combined_df.columns]
        combined_df = combined_df[available_columns]

        logger.info(f"Combined data: {len(combined_df)} total rows, {len(combined_df.columns)} columns")

        # Create table in DuckDB
        conn.execute("DROP TABLE IF EXISTS disease_data")
        conn.register('disease_data_temp', combined_df)
        conn.execute("""
            CREATE TABLE disease_data AS
            SELECT * FROM disease_data_temp
        """)

        # Create indexes for common queries
        conn.execute("CREATE INDEX idx_disease_name ON disease_data(disease_name)")
        conn.execute("CREATE INDEX idx_state ON disease_data(state)")
        conn.execute("CREATE INDEX idx_report_period ON disease_data(report_period_start)")
        conn.execute("CREATE INDEX idx_data_source ON disease_data(data_source)")

        # Unregister temporary view
        conn.unregister('disease_data_temp')

        row_count = conn.execute("SELECT COUNT(*) FROM disease_data").fetchone()[0]
        logger.info(f"Created disease_data table with {row_count} rows (tracker data)")

        # Create disease name mapping table
        self._create_disease_mapping_table()

        self._initialized = True

    def _create_disease_mapping_table(self) -> None:
        """Create and populate the disease name mapping table"""
        conn = self.connect()

        # Create mapping table
        conn.execute("DROP TABLE IF EXISTS disease_name_mapping")
        conn.execute("""
            CREATE TABLE disease_name_mapping (
                tracker_name VARCHAR,
                nndss_name VARCHAR,
                PRIMARY KEY (tracker_name)
            )
        """)

        # Insert mappings
        for tracker_name, nndss_name in TRACKER_TO_NNDSS.items():
            conn.execute(
                "INSERT INTO disease_name_mapping (tracker_name, nndss_name) VALUES (?, ?)",
                [tracker_name, nndss_name]
            )

        mapping_count = conn.execute("SELECT COUNT(*) FROM disease_name_mapping").fetchone()[0]
        logger.info(f"Created disease_name_mapping table with {mapping_count} mappings")

    def load_nndss_csv(self) -> None:
        """Load NNDSS data from CSV into DuckDB (appends to existing disease_data table)"""
        conn = self.connect()

        # Find NNDSS CSV file
        nndss_dir = settings.nndss_data_directory
        if not nndss_dir.exists():
            logger.warning(f"NNDSS data directory not found: {nndss_dir}")
            return

        # Look for NNDSS CSV files
        nndss_files = list(nndss_dir.glob("NNDSS_Weekly_Data_*.csv"))
        if not nndss_files:
            logger.warning(f"No NNDSS CSV files found in {nndss_dir}")
            return

        # Use the most recent file (sorted by name)
        nndss_file = sorted(nndss_files, reverse=True)[0]
        logger.info(f"Loading NNDSS data from {nndss_file}")

        try:
            # Load and transform NNDSS data
            nndss_df = load_nndss_data(nndss_file)
            logger.info(f"Loaded and transformed {len(nndss_df)} NNDSS records")

            # Append to existing disease_data table
            conn.register('nndss_data_temp', nndss_df)
            conn.execute("""
                INSERT INTO disease_data
                SELECT * FROM nndss_data_temp
            """)
            conn.unregister('nndss_data_temp')

            total_count = conn.execute("SELECT COUNT(*) FROM disease_data").fetchone()[0]
            nndss_count = conn.execute("SELECT COUNT(*) FROM disease_data WHERE data_source = 'nndss'").fetchone()[0]
            logger.info(f"Appended NNDSS data: {nndss_count} rows, total table size: {total_count} rows")

        except Exception as e:
            logger.error(f"Error loading NNDSS data: {e}", exc_info=True)

    def get_diseases(self, data_source: str | None = None) -> list[str]:
        """
        Get list of unique diseases in the database

        Args:
            data_source: Filter by data source ('tracker', 'nndss', or None for all)
        """
        if not self._initialized:
            return []

        with self._lock:
            if data_source:
                result = self.conn.execute("""
                    SELECT DISTINCT disease_name
                    FROM disease_data
                    WHERE data_source = ?
                    ORDER BY disease_name
                """, [data_source]).fetchall()
            else:
                result = self.conn.execute("""
                    SELECT DISTINCT disease_name
                    FROM disease_data
                    ORDER BY disease_name
                """).fetchall()

            return [row[0] for row in result]

    def get_states(self, data_source: str | None = None) -> list[str]:
        """
        Get list of unique states in the database

        Args:
            data_source: Filter by data source ('tracker', 'nndss', or None for all)
        """
        if not self._initialized:
            return []

        with self._lock:
            if data_source:
                result = self.conn.execute("""
                    SELECT DISTINCT state
                    FROM disease_data
                    WHERE data_source = ?
                    ORDER BY state
                """, [data_source]).fetchall()
            else:
                result = self.conn.execute("""
                    SELECT DISTINCT state
                    FROM disease_data
                    ORDER BY state
                """).fetchall()

            return [row[0] for row in result]

    def get_summary_stats(self, data_source: str | None = None) -> dict:
        """
        Get summary statistics across all data

        Args:
            data_source: Filter by data source ('tracker', 'nndss', or None for all)
        """
        if not self._initialized:
            return {}

        with self._lock:
            if data_source:
                stats = self.conn.execute("""
                    SELECT
                        COUNT(*) as total_records,
                        COUNT(DISTINCT disease_name) as total_diseases,
                        COUNT(DISTINCT state) as total_states,
                        SUM(count) as total_cases,
                        MIN(report_period_start) as earliest_date,
                        MAX(report_period_end) as latest_date
                    FROM disease_data
                    WHERE data_source = ?
                """, [data_source]).fetchone()
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

            # Get breakdown by data source
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
                "source_breakdown": {row[0]: {"records": row[1], "cases": row[2]} for row in source_breakdown}
            }

    def get_disease_totals(self, data_source: str | None = None) -> list[dict]:
        """
        Get total case counts for each disease

        Args:
            data_source: Filter by data source ('tracker', 'nndss', or None for all)
        """
        if not self._initialized:
            return []

        with self._lock:
            if data_source:
                result = self.conn.execute("""
                    SELECT
                        disease_name,
                        SUM(count) as total_cases
                    FROM disease_data
                    WHERE data_source = ?
                    GROUP BY disease_name
                    ORDER BY disease_name
                """, [data_source]).fetchall()
            else:
                result = self.conn.execute("""
                    SELECT
                        disease_name,
                        SUM(count) as total_cases
                    FROM disease_data
                    GROUP BY disease_name
                    ORDER BY disease_name
                """).fetchall()

            return [{"disease_name": row[0], "total_cases": int(row[1]) if row[1] else 0} for row in result]

    def get_national_disease_timeseries(self, disease_name: str, granularity: str = 'month',
                                       data_source: str | None = None) -> list[dict]:
        """
        Get time series data for a disease aggregated nationally by month or week

        Args:
            disease_name: Name of the disease
            granularity: 'month' or 'week'
            data_source: Filter by data source ('tracker', 'nndss', or None for all)
        """
        if not self._initialized:
            return []

        # Validate granularity (must be literal for DATE_TRUNC)
        if granularity not in ['month', 'week']:
            granularity = 'month'

        with self._lock:
            # Build query with granularity as literal (DuckDB requires this)
            # report_period_start is now a proper TIMESTAMP type from pandas datetime parsing
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

            return [{"period": str(row[0]), "total_cases": int(row[1]) if row[1] else 0} for row in result]

    def get_disease_stats(self, disease_name: str, data_source: str | None = None) -> dict:
        """
        Get summary statistics for a specific disease

        Args:
            disease_name: Name of the disease
            data_source: Filter by data source ('tracker', 'nndss', or None for all)
        """
        if not self._initialized:
            return {}

        with self._lock:
            where_clause = "WHERE disease_name = ?" if not data_source else "WHERE disease_name = ? AND data_source = ?"
            params = [disease_name] if not data_source else [disease_name, data_source]

            # Total cases
            total_cases_result = self.conn.execute(f"""
                SELECT SUM(count) as total_cases
                FROM disease_data
                {where_clause}
            """, params).fetchone()
            total_cases = int(total_cases_result[0]) if total_cases_result[0] else 0

            # Affected states/jurisdictions
            affected_states_result = self.conn.execute(f"""
                SELECT COUNT(DISTINCT state) as affected_states
                FROM disease_data
                {where_clause}
            """, params).fetchone()
            affected_states = int(affected_states_result[0]) if affected_states_result[0] else 0

            # Affected counties/regions (using geo_name column)
            affected_counties_result = self.conn.execute(f"""
                SELECT COUNT(DISTINCT geo_name) as affected_counties
                FROM disease_data
                {where_clause}
                  AND geo_name IS NOT NULL
                  AND geo_name != ''
            """, params).fetchone()
            affected_counties = int(affected_counties_result[0]) if affected_counties_result[0] else 0

            # Latest 2-week cases (last 14 days from the most recent date)
            latest_two_week_result = self.conn.execute(f"""
                WITH latest_date AS (
                    SELECT MAX(report_period_end) as max_date
                    FROM disease_data
                    {where_clause}
                )
                SELECT SUM(count) as two_week_cases
                FROM disease_data
                {where_clause}
                  AND report_period_end >= (SELECT max_date - INTERVAL 14 DAYS FROM latest_date)
                  AND report_period_end <= (SELECT max_date FROM latest_date)
            """, params + params).fetchone()
            two_week_cases = int(latest_two_week_result[0]) if latest_two_week_result[0] else 0

            return {
                "total_cases": total_cases,
                "affected_states": affected_states,
                "affected_counties": affected_counties,
                "two_week_cases": two_week_cases
            }

    def get_age_group_distribution_by_state(self, disease_name: str,
                                            data_source: str | None = None) -> dict:
        """
        Get age group distribution by state for a disease

        Args:
            disease_name: Name of the disease
            data_source: Filter by data source ('tracker', 'nndss', or None for all)
        """
        if not self._initialized:
            return {"states": {}, "age_groups": []}

        with self._lock:
            where_clause = "WHERE disease_name = ?" if not data_source else "WHERE disease_name = ? AND data_source = ?"
            params = [disease_name] if not data_source else [disease_name, data_source]

            # Get list of states with data for this disease
            states_query = f"""
                SELECT DISTINCT state
                FROM disease_data
                {where_clause}
                ORDER BY state
            """
            states_result = self.conn.execute(states_query, params).fetchall()
            available_states = [row[0] for row in states_result]

            # Get age group data by state (excluding totals)
            age_group_query = f"""
                SELECT
                    state,
                    age_group,
                    SUM(count) as total_cases
                FROM disease_data
                {where_clause}
                  AND age_group IS NOT NULL
                  AND age_group != ''
                  AND LOWER(age_group) NOT LIKE '%total%'
                GROUP BY state, age_group
                ORDER BY state, age_group
            """
            age_group_result = self.conn.execute(age_group_query, params).fetchall()

            # Get unique age groups (excluding totals)
            age_groups_query = f"""
                SELECT DISTINCT age_group
                FROM disease_data
                {where_clause}
                  AND age_group IS NOT NULL
                  AND age_group != ''
                  AND LOWER(age_group) NOT LIKE '%total%'
                ORDER BY age_group
            """
            age_groups_result = self.conn.execute(age_groups_query, params).fetchall()
            age_groups = [row[0] for row in age_groups_result]

            # Group by state and calculate percentages
            states_data = {}
            for state in available_states:
                state_total = 0
                state_age_counts = {}

                # First pass: get totals
                for row in age_group_result:
                    if row[0] == state:
                        state_age_counts[row[1]] = int(row[2]) if row[2] else 0
                        state_total += state_age_counts[row[1]]

                # Second pass: calculate percentages
                state_age_percentages = {}
                for age_group in age_groups:
                    count = state_age_counts.get(age_group, 0)
                    percentage = (count / state_total * 100) if state_total > 0 else 0
                    state_age_percentages[age_group] = {
                        "count": count,
                        "percentage": round(percentage, 2)
                    }

                states_data[state] = state_age_percentages

            return {
                "states": states_data,
                "age_groups": age_groups,
                "available_states": available_states
            }

    def get_disease_timeseries_by_state(self, disease_name: str, granularity: str = 'month',
                                        data_source: str | None = None) -> dict:
        """
        Get time series data for a disease broken down by state with national total

        Args:
            disease_name: Name of the disease
            granularity: 'month' or 'week'
            data_source: Filter by data source ('tracker', 'nndss', or None for all)
        """
        if not self._initialized:
            return {"states": [], "national": [], "available_states": []}

        # Validate granularity (must be literal for DATE_TRUNC)
        if granularity not in ['month', 'week']:
            granularity = 'month'

        with self._lock:
            where_clause = "WHERE disease_name = ?" if not data_source else "WHERE disease_name = ? AND data_source = ?"
            params = [disease_name] if not data_source else [disease_name, data_source]

            # Get list of states with data for this disease
            states_query = f"""
                SELECT DISTINCT state
                FROM disease_data
                {where_clause}
                ORDER BY state
            """
            states_result = self.conn.execute(states_query, params).fetchall()
            available_states = [row[0] for row in states_result]

            # Get state-level time series
            state_query = f"""
                SELECT
                    state,
                    DATE_TRUNC('{granularity}', report_period_start) as period,
                    SUM(count) as total_cases
                FROM disease_data
                {where_clause}
                GROUP BY state, DATE_TRUNC('{granularity}', report_period_start)
                ORDER BY state, period ASC
            """
            state_result = self.conn.execute(state_query, params).fetchall()

            # Group by state
            states_data = {}
            for row in state_result:
                state, period, cases = row
                if state not in states_data:
                    states_data[state] = []
                states_data[state].append({
                    "period": str(period),
                    "cases": int(cases) if cases else 0
                })

            # Get national total (same as get_national_disease_timeseries)
            national_query = f"""
                SELECT
                    DATE_TRUNC('{granularity}', report_period_start) as period,
                    SUM(count) as total_cases
                FROM disease_data
                {where_clause}
                GROUP BY DATE_TRUNC('{granularity}', report_period_start)
                ORDER BY period ASC
            """
            national_result = self.conn.execute(national_query, params).fetchall()
            national_data = [{"period": str(row[0]), "cases": int(row[1]) if row[1] else 0} for row in national_result]

            return {
                "states": states_data,
                "national": national_data,
                "available_states": available_states
            }

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Closed DuckDB connection")


# Global database instance
db = DiseaseDatabase()
