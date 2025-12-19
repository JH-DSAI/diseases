# Disease Dashboard ETL Architecture

**Version**: 2.0
**Last Updated**: 2025
**Data Sources**: State Tracker + NNDSS (CDC)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Pattern](#architecture-pattern)
3. [Data Sources](#data-sources)
4. [Database Schema](#database-schema)
5. [ETL Pipeline](#etl-pipeline)
6. [Disease Name Mapping](#disease-name-mapping)
7. [API Design](#api-design)
8. [Query Patterns](#query-patterns)
9. [Data Quality & Validation](#data-quality--validation)
10. [Future Considerations](#future-considerations)

---

## Overview

The Disease Dashboard ingests disease surveillance data from two sources:

1. **State Tracker Data**: High-granularity data from individual states with age group stratification
2. **NNDSS (CDC) Data**: National baseline surveillance data updated weekly

The ETL pipeline follows a **medallion architecture** with a **unified schema** approach, treating CDC NNDSS as the canonical disease naming standard.

### Key Design Decisions

- ✅ **Unified Table**: Single `disease_data` table with `data_source` column
- ✅ **CDC Standard**: NNDSS disease names as canonical reference
- ✅ **Persistent Storage**: DuckDB file (`disease_dashboard.duckdb`)
- ✅ **Bifurcated API**: Separate query parameters for source filtering
- ✅ **Wide Table Design**: Modern analytics-optimized schema

---

## Architecture Pattern

### Medallion Architecture (Simplified)

```
┌─────────────────────────────────────────────────────────┐
│ RAW LAYER (File System)                                 │
├─────────────────────────────────────────────────────────┤
│ • us_disease_tracker_data/data/states/**/*.csv          │
│ • nndss_data/NNDSS_Weekly_Data_*.csv                    │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│ SILVER LAYER (Transformed)                              │
├─────────────────────────────────────────────────────────┤
│ Transformers:                                            │
│ • app/database.py::load_csv_files() → tracker data      │
│ • app/nndss_loader.py::NNDSSTransformer → NNDSS data    │
│                                                          │
│ Transformations:                                         │
│ • Disease name normalization (tracker → NNDSS names)    │
│ • MMWR week → date range conversion                     │
│ • Data source tagging                                   │
│ • Schema unification                                    │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│ GOLD LAYER (Analytics-Ready)                            │
├─────────────────────────────────────────────────────────┤
│ Database: disease_dashboard.duckdb                      │
│                                                          │
│ Tables:                                                  │
│ • disease_data (unified, indexed)                       │
│ • disease_name_mapping                                  │
│                                                          │
│ Served via: FastAPI REST endpoints                      │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
Tracker CSVs ──┐
               ├──> [Normalize Names] ──┐
NNDSS CSV ─────┤                        ├──> [Unified Schema] ──> DuckDB ──> API
               └──> [Parse MMWR Weeks]──┘
```

---

## Data Sources

### 1. State Tracker Data

**Location**: `/us_disease_tracker_data/data/states/`

**Structure**: State-organized directories with timestamped CSV files

```
us_disease_tracker_data/
└── data/
    └── states/
        ├── ID/
        │   └── 20251119-174839_ID_user.csv
        ├── IL/
        │   └── 20251119-174839_IL_user.csv
        └── MA/
            └── 20251119-174839_MA_user.csv
```

**File Naming**: `YYYYMMDD-HHMMSS_STATE_UPLOADERNAME.csv`

**Loading Strategy**: Latest file per state (sorted by timestamp)

**Characteristics**:
- Granularity: State, County, Age Groups
- Temporal: Weekly/Monthly (flexible)
- Diseases: 3 tracked (measles, meningococcus, pertussis)
- Age Stratification: ✅ Yes
- Confirmation Status: ✅ Yes (confirmed/probable)
- File Count: ~3-5 per state
- Total Size: ~100KB-1MB per state

### 2. NNDSS (CDC) Data

**Location**: `/nndss_data/`

**Structure**: Single weekly CSV file

```
nndss_data/
└── NNDSS_Weekly_Data_20251121.csv  (220.1 MB)
```

**File Naming**: `NNDSS_Weekly_Data_YYYYMMDD.csv`

**Loading Strategy**: Most recent file (sorted by filename)

**Characteristics**:
- Granularity: National, Regional, State
- Temporal: Weekly (MMWR weeks)
- Diseases: 50+ diseases
- Age Stratification: ❌ No
- Confirmation Status: ❌ Not specified
- Record Count: ~1.5M rows
- Geographic Levels:
  - National: US RESIDENTS, NON-US RESIDENTS, TOTAL
  - Regional: 10 HHS regions (NEW ENGLAND, MIDDLE ATLANTIC, etc.)
  - State: All 50 states + DC + territories

**MMWR Week System**: Epidemiological weeks starting on Sunday, where week 1 begins on the first Sunday with at least 4 days in the new year.

---

## Database Schema

### Unified Table: `disease_data`

Modern **wide table design** optimized for analytical queries.

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| `report_period_start` | TIMESTAMP | Start of reporting period | Both |
| `report_period_end` | TIMESTAMP | End of reporting period | Both |
| `date_type` | VARCHAR | Date classification (cccd, mmwr) | Both |
| `time_unit` | VARCHAR | Granularity (week, month) | Both |
| `disease_name` | VARCHAR | **CDC NNDSS canonical name** | Both (mapped) |
| `disease_subtype` | VARCHAR | Disease variant/subtype | Tracker |
| `state` | VARCHAR | 2-letter state code | Both |
| `reporting_jurisdiction` | VARCHAR | Reporting authority | Both |
| `geo_name` | VARCHAR | Geographic area name | Both |
| `geo_unit` | VARCHAR | Geographic level (state, county, region, national) | Both |
| `age_group` | VARCHAR | Age bracket (e.g., ">=65 y") | Tracker only |
| `confirmation_status` | VARCHAR | Case confirmation level | Tracker only |
| `outcome` | VARCHAR | Measurement type ("cases") | Both |
| `count` | INTEGER | Number of cases | Both |
| **`data_source`** | VARCHAR | Source identifier ("tracker", "nndss") | **Metadata** |
| **`original_disease_name`** | VARCHAR | Pre-mapping disease name | **Provenance** |

**Indexes**:
- `idx_disease_name` on `disease_name`
- `idx_state` on `state`
- `idx_report_period` on `report_period_start`
- `idx_data_source` on `data_source`

### Mapping Table: `disease_name_mapping`

| Column | Type | Description |
|--------|------|-------------|
| `tracker_name` | VARCHAR (PK) | Original tracker disease name |
| `nndss_name` | VARCHAR | CDC NNDSS standard name |

**Current Mappings**:

| Tracker Name | NNDSS Name (CDC Standard) |
|--------------|---------------------------|
| `measles` | `Measles` |
| `meningococcus` | `Meningococcal disease` |
| `pertussis` | `Pertussis` |

---

## ETL Pipeline

### Stage 1: Tracker Data Loading

**File**: `app/database.py::load_csv_files()`

**Process**:

```python
1. Scan directory: us_disease_tracker_data/data/states/
2. Group by state: { 'MA': [file1, file2], 'IL': [file3] }
3. Select latest per state: Sort by filename timestamp DESC
4. Load CSVs with pandas:
   - Parse date columns: report_period_start, report_period_end
   - Read into DataFrame
5. Transform:
   - Store original_disease_name
   - Map disease names: tracker → NNDSS (via TRACKER_TO_NNDSS dict)
   - Add data_source = 'tracker'
6. Concat all DataFrames
7. Register with DuckDB and create table
8. Create indexes
```

**Key Code**:

```python
# Disease name mapping
combined_df['original_disease_name'] = combined_df['disease_name']
combined_df['disease_name'] = combined_df['disease_name'].apply(
    lambda name: TRACKER_TO_NNDSS.get(name.lower(), name)
)
combined_df['data_source'] = 'tracker'
```

### Stage 2: NNDSS Data Loading

**File**: `app/nndss_loader.py::NNDSSTransformer`

**Process**:

```python
1. Locate CSV: nndss_data/NNDSS_Weekly_Data_*.csv (most recent)
2. Load with pandas:
   - Handle empty values as NULL
   - String types for cleaning
3. Transform:
   a. Classify geo_unit:
      - "US RESIDENTS" → national
      - "NEW ENGLAND" → region
      - "MASSACHUSETTS" → state
   b. Parse MMWR weeks → date ranges:
      - Calculate Sunday start of MMWR week
      - End date = start + 6 days
   c. Clean case counts:
      - Convert "Current week" column to integer
      - Handle blanks, "-", non-numeric values → NULL
   d. Normalize disease names:
      - Store original in original_disease_name
      - Use Label as-is for disease_name
   e. Create state codes:
      - Map full state names → 2-letter codes
      - Regional records keep region name
   f. Map to unified schema:
      - Add data_source = 'nndss'
      - Set age_group = NULL, confirmation_status = NULL
4. Filter: Remove rows with NULL count
5. Append to DuckDB disease_data table
```

**MMWR Week Calculation**:

```python
def get_mmwr_week_start(year: int, week: int) -> datetime:
    """
    MMWR weeks start on Sunday.
    Week 1 is the first week with at least 4 days in the year.
    """
    jan1 = datetime(year, 1, 1)
    days_until_sunday = (6 - jan1.weekday()) % 7
    first_sunday = jan1 + timedelta(days=days_until_sunday)

    if jan1.weekday() <= 3:  # Sun-Wed
        week1_start = first_sunday
    else:  # Thu-Sat
        week1_start = first_sunday + timedelta(days=7)

    return week1_start + timedelta(weeks=(week - 1))
```

### Stage 3: Startup Sequence

**File**: `app/main.py::lifespan()`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db.connect()
    db.load_csv_files()      # Load tracker data
    db.load_nndss_csv()      # Append NNDSS data

    stats = db.get_summary_stats()
    logger.info(f"Loaded {stats['total_records']} total records")
    for source, counts in stats['source_breakdown'].items():
        logger.info(f"  - {source}: {counts['records']} records")

    yield

    # Shutdown
    db.close()
```

---

## Disease Name Mapping

### Rationale

**Problem**: Different naming conventions between data sources

- Tracker: `"measles"` (lowercase)
- NNDSS: `"Measles"` (title case), also encodes subtypes in labels like `"Measles, Imported"`

**Solution**: Treat NNDSS (CDC) as canonical standard, with transformations to extract subtypes

**Benefits**:
- ✅ Official CDC nomenclature
- ✅ Consistent with national reporting
- ✅ Future-proof for additional NNDSS diseases
- ✅ Clear provenance tracking via `original_disease_name`
- ✅ Proper subtype extraction for serogroups

### Implementation

**File**: `app/etl/normalizers/disease_names.py`

```python
# Tracker to NNDSS mapping
TRACKER_TO_NNDSS = {
    "measles": "Measles",
    "meningococcus": "Meningococcal disease",
    "pertussis": "Pertussis",
}

# NNDSS label to (disease_name, disease_subtype) transformations
NNDSS_DISEASE_TRANSFORMS = {
    "Measles, Imported": ("Measles", None),
    "Measles, Indigenous": ("Measles", None),
    "Meningococcal disease, Serogroup B": ("Meningococcal disease", "B"),
    "Meningococcal disease, Serogroups ACWY": ("Meningococcal disease", "ACWY"),
    "Meningococcal disease, Other serogroups": ("Meningococcal disease", "Other"),
    "Meningococcal disease, Unknown serogroup": ("Meningococcal disease", "Unknown"),
    "Meningococcal disease, All serogroups": ("Meningococcal disease", None),
}
```

**Applied During**:
- Tracker data loading: `normalize_tracker_disease_name()`
- NNDSS data loading: `normalize_nndss_disease_name()` + `transform_nndss_disease()`

**Stored As**:
- `disease_data.disease_name` → NNDSS canonical name
- `disease_data.disease_subtype` → Extracted subtype (serogroup, etc.)
- `disease_data.original_disease_name` → Original source name
- `disease_name_mapping` table → Persistent lookup

See `/docs/data-decisions.md` for rationale on aggregation decisions.

---

## API Design

### Unified Endpoints with Source Filtering

**Pattern**: Optional `?data_source=` query parameter on all endpoints

```
/api/diseases?data_source=tracker
/api/diseases?data_source=nndss
/api/diseases  (default: all sources)
```

### Endpoints

| Endpoint | Method | Query Params | Description |
|----------|--------|--------------|-------------|
| `/api/health` | GET | - | Service health check |
| `/api/diseases` | GET | `data_source` | List diseases |
| `/api/stats` | GET | `data_source` | Summary statistics |
| `/api/timeseries/national/{disease}` | GET | `granularity`, `data_source` | National trend |
| `/api/timeseries/states/{disease}` | GET | `granularity`, `data_source` | State breakdown |
| `/api/disease/{disease}/stats` | GET | `data_source` | Disease summary |
| `/api/disease/{disease}/age-groups` | GET | `data_source` | Age distribution |

### Example Queries

```bash
# All diseases (both sources)
GET /api/diseases

# Only NNDSS diseases
GET /api/diseases?data_source=nndss

# Pertussis trend from tracker data only
GET /api/timeseries/national/Pertussis?granularity=week&data_source=tracker

# Measles age distribution (only tracker has age data)
GET /api/disease/Measles/age-groups?data_source=tracker
```

### Response Structure

All responses include `source_breakdown` in summary stats:

```json
{
  "total_records": 1572971,
  "total_diseases": 52,
  "total_cases": 8453921,
  "source_breakdown": {
    "tracker": {
      "records": 178,
      "cases": 1234
    },
    "nndss": {
      "records": 1572793,
      "cases": 8452687
    }
  }
}
```

---

## Query Patterns

### Pattern 1: Source-Specific Queries

**Use Case**: Compare same disease across sources

```sql
-- Tracker data only
SELECT disease_name, SUM(count) as total_cases
FROM disease_data
WHERE data_source = 'tracker' AND disease_name = 'Pertussis'
GROUP BY disease_name;

-- NNDSS data only
SELECT disease_name, SUM(count) as total_cases
FROM disease_data
WHERE data_source = 'nndss' AND disease_name = 'Pertussis'
GROUP BY disease_name;
```

### Pattern 2: Combined Analytics

**Use Case**: Unified view merging both sources

```sql
-- National total (all sources)
SELECT
    DATE_TRUNC('month', report_period_start) as period,
    SUM(count) as total_cases
FROM disease_data
WHERE disease_name = 'Measles'
GROUP BY DATE_TRUNC('month', report_period_start)
ORDER BY period;
```

### Pattern 3: Filler Pattern

**Use Case**: NNDSS as baseline until state data available

```sql
-- Prioritize tracker, fallback to NNDSS
WITH latest_tracker_date AS (
    SELECT MAX(report_period_end) as max_date
    FROM disease_data
    WHERE data_source = 'tracker'
),
data_with_priority AS (
    SELECT *,
        CASE
            WHEN data_source = 'tracker' THEN 1
            WHEN data_source = 'nndss' AND report_period_end <=
                (SELECT max_date FROM latest_tracker_date) THEN 2
            ELSE 3
        END as priority
    FROM disease_data
)
SELECT * FROM data_with_priority
WHERE priority <= 2
ORDER BY state, report_period_start, priority;
```

### Pattern 4: Geo-Level Filtering

**Use Case**: Regional analysis (NNDSS only has this)

```sql
-- Regional trends (NNDSS only)
SELECT geo_name, DATE_TRUNC('month', report_period_start) as period, SUM(count)
FROM disease_data
WHERE data_source = 'nndss'
  AND geo_unit = 'region'
  AND disease_name = 'Measles'
GROUP BY geo_name, period
ORDER BY geo_name, period;
```

### Pattern 5: Age Stratification

**Use Case**: Age group analysis (tracker only has this)

```sql
-- Age distribution (tracker only)
SELECT age_group, SUM(count) as cases
FROM disease_data
WHERE data_source = 'tracker'
  AND disease_name = 'Meningococcal disease'
  AND age_group IS NOT NULL
GROUP BY age_group;
```

---

## Data Quality & Validation

### Tracker Data Validation

**Checks**:
- ✅ CSV file exists for each state
- ✅ Date columns parse as datetime
- ✅ Disease names in mapping dictionary
- ✅ Count values are numeric

**Handling**:
- Missing files: Log warning, skip state
- Parse errors: Log error, skip file
- Unknown disease: Keep original name

### NNDSS Data Validation

**Checks**:
- ✅ MMWR week 1-53
- ✅ MMWR year valid
- ✅ Current week is numeric or NULL
- ✅ State names in mapping dictionary

**Handling**:
- Invalid MMWR weeks: Set date to NULL
- Invalid counts: Set count to NULL, filter later
- Unknown states: Keep as-is (may be region/territory)

### Data Quality Metrics

**Tracked in Logs**:

```
INFO: Loaded 178 raw tracker records
INFO: Transformed to 178 records in unified schema
INFO: Loaded 1572971 raw NNDSS records
INFO: Transformed to 456789 records in unified schema (filtered aggregates/nulls)
INFO: Created disease_data table with 457067 rows
INFO:   - tracker: 178 records, 1234 cases
INFO:   - nndss: 456789 records, 8452687 cases
```

---

## Mixed Sources Deduplication

For diseases that have data from both tracker and NNDSS sources, a merged view (`disease_data_merged`) is created to avoid double-counting when displaying combined totals.

### Deduplication Logic

The view applies a **filler pattern** where tracker data takes priority:

1. **Aggregate to monthly state level**: All records are aggregated by (disease, state, month)
   - Tracker county-level data → summed to state level
   - Tracker age groups → summed to total
   - NNDSS weekly data → summed to monthly

2. **Apply source priority**: For each (disease, state, month) combination, only one source's data is kept
   - Priority 1: Tracker data
   - Priority 2: NNDSS data

3. **Result**: A deduplicated dataset where:
   - States with tracker data use tracker values
   - States without tracker data use NNDSS values (gap filling)

### SQL Implementation

```sql
CREATE VIEW disease_data_merged AS
WITH monthly_aggregated AS (
    SELECT
        disease_name, disease_slug, state,
        DATE_TRUNC('month', report_period_start) as month,
        data_source, SUM(count) as count
    FROM disease_data
    WHERE state IS NOT NULL AND state != ''
    GROUP BY disease_name, disease_slug, state,
             DATE_TRUNC('month', report_period_start), data_source
),
ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY disease_name, state, month
            ORDER BY CASE WHEN data_source = 'tracker' THEN 1 ELSE 2 END
        ) as rn
    FROM monthly_aggregated
)
SELECT disease_name, disease_slug, state, month, data_source, count
FROM ranked WHERE rn = 1
```

### Usage

The merged view is used automatically when querying without a `data_source` filter:
- Homepage disease totals
- Disease detail page statistics
- Choropleth map state totals

When a specific `data_source` is specified (e.g., "tracker" or "nndss"), queries use the raw `disease_data` table directly.

See `/docs/data-decisions.md` for the rationale behind this approach.

---

## Future Considerations

### Potential Enhancements

1. **Temporal Validity**
   - Add `valid_from`, `valid_to` columns
   - Track when tracker data supersedes NNDSS for same period

2. **Data Lineage**
   - Add `load_timestamp` column
   - Track which CSV file each record came from

3. **Incremental Updates**
   - Change-data-capture for tracker files
   - Only load new/updated records

4. **Schema Evolution**
   - Add `schema_version` column
   - Support backwards compatibility

5. **Additional Sources**
   - Framework extensible to new sources
   - Add `source_metadata` JSONB column

6. **Data Quality Dashboard**
   - Visualization of coverage gaps
   - Freshness metrics per state
   - Mapping completion tracking

7. **Advanced Filler Logic**
   - Automated detection of when to use NNDSS vs tracker
   - Smart merging based on data freshness
   - Gap-filling algorithms

---

## Appendix: File Reference

### Core ETL Files

- `app/config.py` - Configuration settings
- `app/database.py` - DuckDB connection, table creation, query methods
- `app/disease_mappings.py` - Disease name normalization dictionary
- `app/nndss_loader.py` - NNDSS transformation logic
- `app/models.py` - API response schemas
- `app/routers/api.py` - API endpoints
- `app/main.py` - Application startup/shutdown

### Data Directories

- `/us_disease_tracker_data/data/states/` - State tracker CSVs
- `/nndss_data/` - NNDSS weekly CSV
- `disease_dashboard.duckdb` - Persistent database file

---

**Document End**
