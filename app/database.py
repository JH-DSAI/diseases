"""DuckDB database connection and data loading"""

import logging

import duckdb
import pandas as pd

from app.config import settings

logger = logging.getLogger(__name__)


class DiseaseDatabase:
    """Manages DuckDB connection and disease data loading"""

    def __init__(self):
        self.conn: duckdb.DuckDBPyConnection | None = None
        self._initialized = False

    def connect(self) -> duckdb.DuckDBPyConnection:
        """Establish DuckDB connection"""
        if self.conn is None:
            self.conn = duckdb.connect(settings.database_path)
            logger.info(f"Connected to DuckDB: {settings.database_path}")
        return self.conn

    def load_csv_files(self) -> None:
        """Load all CSV files from data directory into DuckDB"""
        if self._initialized:
            logger.info("Database already initialized")
            return

        conn = self.connect()
        data_dir = settings.data_directory / "data" / "states"

        if not data_dir.exists():
            logger.warning(f"Data directory not found: {data_dir}")
            return

        # Find all CSV files
        csv_files = list(data_dir.rglob("*.csv"))
        logger.info(f"Found {len(csv_files)} CSV files")

        if not csv_files:
            logger.warning("No CSV files found to load")
            return

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

        # Ensure consistent column order
        expected_columns = [
            'report_period_start', 'report_period_end', 'date_type', 'time_unit',
            'disease_name', 'disease_subtype', 'reporting_jurisdiction', 'state',
            'geo_name', 'geo_unit', 'age_group', 'confirmation_status', 'outcome', 'count'
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

        # Unregister temporary view
        conn.unregister('disease_data_temp')

        row_count = conn.execute("SELECT COUNT(*) FROM disease_data").fetchone()[0]
        logger.info(f"Created disease_data table with {row_count} rows")

        self._initialized = True

    def get_diseases(self) -> list[str]:
        """Get list of unique diseases in the database"""
        if not self._initialized:
            return []

        result = self.conn.execute("""
            SELECT DISTINCT disease_name
            FROM disease_data
            ORDER BY disease_name
        """).fetchall()

        return [row[0] for row in result]

    def get_states(self) -> list[str]:
        """Get list of unique states in the database"""
        if not self._initialized:
            return []

        result = self.conn.execute("""
            SELECT DISTINCT state
            FROM disease_data
            ORDER BY state
        """).fetchall()

        return [row[0] for row in result]

    def get_summary_stats(self) -> dict:
        """Get summary statistics across all data"""
        if not self._initialized:
            return {}

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

        return {
            "total_records": stats[0],
            "total_diseases": stats[1],
            "total_states": stats[2],
            "total_cases": stats[3],
            "earliest_date": stats[4],
            "latest_date": stats[5],
            "disease_totals": self.get_disease_totals()
        }

    def get_disease_totals(self) -> list[dict]:
        """Get total case counts for each disease"""
        if not self._initialized:
            return []

        result = self.conn.execute("""
            SELECT
                disease_name,
                SUM(count) as total_cases
            FROM disease_data
            GROUP BY disease_name
            ORDER BY disease_name
        """).fetchall()

        return [{"disease_name": row[0], "total_cases": int(row[1]) if row[1] else 0} for row in result]

    def get_national_disease_timeseries(self, disease_name: str, granularity: str = 'month') -> list[dict]:
        """Get time series data for a disease aggregated nationally by month or week"""
        if not self._initialized:
            return []

        # Validate granularity (must be literal for DATE_TRUNC)
        if granularity not in ['month', 'week']:
            granularity = 'month'

        # Build query with granularity as literal (DuckDB requires this)
        # report_period_start is now a proper TIMESTAMP type from pandas datetime parsing
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

    def get_disease_stats(self, disease_name: str) -> dict:
        """Get summary statistics for a specific disease"""
        if not self._initialized:
            return {}

        # Total cases
        total_cases_result = self.conn.execute("""
            SELECT SUM(count) as total_cases
            FROM disease_data
            WHERE disease_name = ?
        """, [disease_name]).fetchone()
        total_cases = int(total_cases_result[0]) if total_cases_result[0] else 0

        # Affected states/jurisdictions
        affected_states_result = self.conn.execute("""
            SELECT COUNT(DISTINCT state) as affected_states
            FROM disease_data
            WHERE disease_name = ?
        """, [disease_name]).fetchone()
        affected_states = int(affected_states_result[0]) if affected_states_result[0] else 0

        # Affected counties/regions (using geo_name column)
        affected_counties_result = self.conn.execute("""
            SELECT COUNT(DISTINCT geo_name) as affected_counties
            FROM disease_data
            WHERE disease_name = ?
              AND geo_name IS NOT NULL
              AND geo_name != ''
        """, [disease_name]).fetchone()
        affected_counties = int(affected_counties_result[0]) if affected_counties_result[0] else 0

        # Latest 2-week cases (last 14 days from the most recent date)
        latest_two_week_result = self.conn.execute("""
            WITH latest_date AS (
                SELECT MAX(report_period_end) as max_date
                FROM disease_data
                WHERE disease_name = ?
            )
            SELECT SUM(count) as two_week_cases
            FROM disease_data
            WHERE disease_name = ?
              AND report_period_end >= (SELECT max_date - INTERVAL 14 DAYS FROM latest_date)
              AND report_period_end <= (SELECT max_date FROM latest_date)
        """, [disease_name, disease_name]).fetchone()
        two_week_cases = int(latest_two_week_result[0]) if latest_two_week_result[0] else 0

        return {
            "total_cases": total_cases,
            "affected_states": affected_states,
            "affected_counties": affected_counties,
            "two_week_cases": two_week_cases
        }

    def get_age_group_distribution_by_state(self, disease_name: str) -> dict:
        """Get age group distribution by state for a disease"""
        if not self._initialized:
            return {"states": {}, "age_groups": []}

        # Get list of states with data for this disease
        states_query = """
            SELECT DISTINCT state
            FROM disease_data
            WHERE disease_name = ?
            ORDER BY state
        """
        states_result = self.conn.execute(states_query, [disease_name]).fetchall()
        available_states = [row[0] for row in states_result]

        # Get age group data by state (excluding totals)
        age_group_query = """
            SELECT
                state,
                age_group,
                SUM(count) as total_cases
            FROM disease_data
            WHERE disease_name = ?
              AND age_group IS NOT NULL
              AND age_group != ''
              AND LOWER(age_group) NOT LIKE '%total%'
            GROUP BY state, age_group
            ORDER BY state, age_group
        """
        age_group_result = self.conn.execute(age_group_query, [disease_name]).fetchall()

        # Get unique age groups (excluding totals)
        age_groups_query = """
            SELECT DISTINCT age_group
            FROM disease_data
            WHERE disease_name = ?
              AND age_group IS NOT NULL
              AND age_group != ''
              AND LOWER(age_group) NOT LIKE '%total%'
            ORDER BY age_group
        """
        age_groups_result = self.conn.execute(age_groups_query, [disease_name]).fetchall()
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

    def get_disease_timeseries_by_state(self, disease_name: str, granularity: str = 'month') -> dict:
        """Get time series data for a disease broken down by state with national total"""
        if not self._initialized:
            return {"states": [], "national": [], "available_states": []}

        # Validate granularity (must be literal for DATE_TRUNC)
        if granularity not in ['month', 'week']:
            granularity = 'month'

        # Get list of states with data for this disease
        states_query = """
            SELECT DISTINCT state
            FROM disease_data
            WHERE disease_name = ?
            ORDER BY state
        """
        states_result = self.conn.execute(states_query, [disease_name]).fetchall()
        available_states = [row[0] for row in states_result]

        # Get state-level time series
        state_query = f"""
            SELECT
                state,
                DATE_TRUNC('{granularity}', report_period_start) as period,
                SUM(count) as total_cases
            FROM disease_data
            WHERE disease_name = ?
            GROUP BY state, DATE_TRUNC('{granularity}', report_period_start)
            ORDER BY state, period ASC
        """
        state_result = self.conn.execute(state_query, [disease_name]).fetchall()

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
            WHERE disease_name = ?
            GROUP BY DATE_TRUNC('{granularity}', report_period_start)
            ORDER BY period ASC
        """
        national_result = self.conn.execute(national_query, [disease_name]).fetchall()
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
