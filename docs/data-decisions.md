# Data Decisions

This document records key data architecture decisions for the Disease Dashboard.

---

## Mixed Sources Deduplication

**Decision Date**: 2025-12-18

### Context

The dashboard ingests disease surveillance data from two sources:
- **Tracker**: State-submitted data with monthly granularity, age groups, and county-level breakdowns
- **NNDSS (CDC)**: National surveillance data with weekly granularity, state-level only

For diseases that have data from both sources (e.g., Pertussis), we need to avoid double-counting when displaying combined totals.

### Decision

Use a **filler pattern** with tracker data taking priority:

For each **(state, month)** combination:
1. If tracker data exists → use tracker value (sum of all tracker records for that state/month)
2. If only NNDSS data exists → use NNDSS value (sum of weekly NNDSS records for that month)
3. Sum all (state, month) values to get the total

### Rationale

- **Tracker data is more authoritative**: State-submitted data is typically more complete and vetted
- **Gap filling**: NNDSS provides broader coverage for states not yet submitting tracker data
- **Monthly aggregation**: Normalizes the different time granularities (tracker monthly vs NNDSS weekly)
- **State-level priority**: Handles tracker county-level data by aggregating to state level before comparison

### Implementation

A `disease_data_merged` view is created in the database that:
1. Aggregates all records to (disease, state, month) level
2. Ranks records by source priority (tracker=1, nndss=2)
3. Keeps only the highest-priority record per (disease, state, month)

This view is used for "mixed sources" queries (when no specific data_source filter is applied).

### Affected Queries

- Homepage disease totals
- Disease detail page statistics
- Choropleth map state totals
- Summary statistics

### Future Considerations

- If NNDSS adds more granular (weekly) views, the aggregation logic may need adjustment
- If tracker data expands to weekly granularity, the normalization period could be changed

---

## NNDSS Disease Name Aggregation

**Decision Date**: 2025-12-19

### Context

NNDSS encodes disease subtypes within the Label field using comma-separated values:
- "Measles, Imported" / "Measles, Indigenous"
- "Meningococcal disease, Serogroup B" / "Meningococcal disease, Serogroups ACWY" / etc.

Tracker data uses a separate `disease_subtype` column:
- `disease_name`: "meningococcus" (mapped to "Meningococcal disease")
- `disease_subtype`: "b", "c", "y", "other", "na"

For proper data merging between sources, NNDSS labels need to be split into `disease_name` and `disease_subtype` fields.

### Decision

#### Measles
**Action**: Aggregate imported/indigenous variants into "Measles" with NULL subtype.

| NNDSS Label | → disease_name | → disease_subtype |
|-------------|----------------|-------------------|
| "Measles, Imported" | "Measles" | NULL |
| "Measles, Indigenous" | "Measles" | NULL |

**Rationale**: Import status is epidemiological metadata indicating where exposure occurred, not a clinical subtype of the disease. Cases should be aggregated for total counts. The original label is preserved in `original_disease_name` for provenance.

#### Meningococcal Disease
**Action**: Extract serogroup into `disease_subtype` and normalize to canonical values.

Canonical serogroup values: `A`, `B`, `C`, `W`, `X`, `Y`, `Z`, `unknown`, `unspecified`

| NNDSS Label | → disease_name | → disease_subtype |
|-------------|----------------|-------------------|
| "Meningococcal disease, Serogroup B" | "meningococcus" | "B" |
| "Meningococcal disease, Serogroups ACWY" | "meningococcus" | "ACWY" |
| "Meningococcal disease, Other serogroups" | "meningococcus" | "unspecified" |
| "Meningococcal disease, Unknown serogroup" | "meningococcus" | "unknown" |
| "Meningococcal disease, All serogroups" | "meningococcus" | NULL |

**Rationale**: Serogroups are clinically significant subtypes that affect vaccine recommendations and outbreak response. "All serogroups" is an aggregate row that should not have a subtype to avoid double-counting. "Other serogroups" maps to "unspecified" to match tracker terminology.

### Serogroup Granularity

**Issue**: NNDSS groups A, C, W, Y serogroups together as "ACWY", while tracker data (e.g., IL) reports C, Y separately.

**Decision**: Preserve tracker granularity where available, normalize non-specific values.

| Source | disease_subtype | Notes |
|--------|-----------------|-------|
| Tracker | B, C, W, Y | Individual serogroups |
| Tracker | unknown | Unknown serogroup |
| Tracker | unspecified | Previously "other" or "na" |
| NNDSS | B | Matches Tracker B |
| NNDSS | ACWY | Combined serogroups (no tracker equivalent) |
| NNDSS | unknown | Normalized from "Unknown serogroup" |
| NNDSS | unspecified | Normalized from "Other serogroups" |

**Tradeoff**: The Serogroup Distribution chart will only display data for states that provide tracker data with individual serogroup breakdowns. States with only NNDSS data will show "ACWY" as a combined category.

### Implementation

Configuration in `app/etl/transformers/nndss.py`:
- `SUBTYPE_PREFIXES`: List of prefixes to strip ("Serogroup ", "Serogroups ")
- `AGGREGATE_SUBTYPES`: Set of subtype values that should become NULL
- `SUBTYPE_NORMALIZATION`: Dict mapping raw values to canonical values

Configuration in `app/etl/transformers/tracker.py`:
- `SUBTYPE_NORMALIZATION`: Dict mapping raw values to canonical values

| Raw Value | → Canonical |
|-----------|-------------|
| "other" | "unspecified" |
| "na" | "unspecified" |
| "not specified" | "unspecified" |
| "n/a" | "unspecified" |
| "unknown" | "unknown" |

Applied in transformers:
- NNDSS: `_parse_nndss_label()` strips prefixes/suffixes, normalizes values
- Tracker: `_normalize_subtype()` normalizes raw values to canonical form

### Affected Data

- NNDSS disease data loading
- Disease name normalization for merging with tracker data
- Serogroup distribution visualizations (limited to tracker data for individual serogroups)
