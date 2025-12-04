"""JSON API endpoints"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth import verify_api_key
from app.config import settings
from app.database import db
from app.dependencies import get_disease_name_or_404, run_db_query
from app.models import (
    AgeGroupData,
    AgeGroupDistributionResponse,
    DiseaseListItem,
    DiseaseListResponse,
    DiseaseStatsResponse,
    DiseaseTimeSeriesByStateResponse,
    DiseaseTotalItem,
    HealthResponse,
    NationalDiseaseTimeSeriesDataPoint,
    NationalDiseaseTimeSeriesResponse,
    StateTimeSeriesDataPoint,
    SummaryStatsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/data",
    tags=["data-api"],
    dependencies=[Depends(verify_api_key)]
)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify service is running.

    Returns:
        Service status and version information
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        database_initialized=db.is_initialized()
    )


@router.get("/diseases", response_model=DiseaseListResponse)
async def list_diseases(data_source: str | None = None):
    """
    Get list of all diseases tracked in the database.

    Args:
        data_source: Optional filter by data source ('tracker', 'nndss', or None for all)

    Returns:
        List of diseases with names and slugs
    """
    try:
        diseases = await run_db_query(db.get_diseases_with_slugs, data_source=data_source)
        return DiseaseListResponse(
            diseases=[DiseaseListItem(name=d["name"], slug=d["slug"]) for d in diseases],
            count=len(diseases)
        )
    except Exception as e:
        logger.error(f"Error fetching diseases: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch diseases") from e


@router.get("/stats", response_model=SummaryStatsResponse)
async def get_summary_stats(data_source: str | None = None):
    """
    Get summary statistics across all disease data.

    Args:
        data_source: Optional filter by data source ('tracker', 'nndss', or None for all)

    Returns:
        Summary statistics including total cases, date ranges, etc.
    """
    try:
        stats = await run_db_query(db.get_summary_stats, data_source=data_source)
        return SummaryStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics") from e


@router.get("/timeseries/national/{disease_slug}", response_model=NationalDiseaseTimeSeriesResponse)
async def get_national_disease_timeseries(disease_slug: str, granularity: str = 'month',
                                         data_source: str | None = None):
    """
    Get national time series data for a specific disease.

    Args:
        disease_slug: URL-safe slug for the disease
        granularity: Time granularity ('month' or 'week'), defaults to 'month'
        data_source: Optional filter by data source ('tracker', 'nndss', or None for all)

    Returns:
        Time series data points with period and total national cases
    """
    try:
        disease_name = await get_disease_name_or_404(disease_slug)
        data = await run_db_query(db.get_national_disease_timeseries, disease_name, granularity, data_source=data_source)

        return NationalDiseaseTimeSeriesResponse(
            disease_name=disease_name,
            disease_slug=disease_slug,
            granularity=granularity,
            data=[NationalDiseaseTimeSeriesDataPoint(**point) for point in data]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching timeseries for {disease_slug}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch time series data") from e


@router.get("/timeseries/states/{disease_slug}", response_model=DiseaseTimeSeriesByStateResponse)
async def get_disease_timeseries_by_state(disease_slug: str, granularity: str = 'month',
                                         data_source: str | None = None):
    """
    Get state-level time series data for a specific disease.

    Args:
        disease_slug: URL-safe slug for the disease
        granularity: Time granularity ('month' or 'week'), defaults to 'month'
        data_source: Optional filter by data source ('tracker', 'nndss', or None for all)

    Returns:
        Time series data broken down by state plus national total
    """
    try:
        disease_name = await get_disease_name_or_404(disease_slug)
        data = await run_db_query(db.get_disease_timeseries_by_state, disease_name, granularity, data_source=data_source)

        # Convert states data to proper format
        states_formatted = {}
        for state, state_data in data["states"].items():
            states_formatted[state] = [StateTimeSeriesDataPoint(**point) for point in state_data]

        # Convert national data to proper format
        national_formatted = [StateTimeSeriesDataPoint(**point) for point in data["national"]]

        return DiseaseTimeSeriesByStateResponse(
            disease_name=disease_name,
            disease_slug=disease_slug,
            granularity=granularity,
            available_states=data["available_states"],
            states=states_formatted,
            national=national_formatted
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching state timeseries for {disease_slug}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch state time series data") from e


@router.get("/disease/{disease_slug}/stats", response_model=DiseaseStatsResponse)
async def get_disease_stats(disease_slug: str, data_source: str | None = None):
    """
    Get summary statistics for a specific disease.

    Args:
        disease_slug: URL-safe slug for the disease
        data_source: Optional filter by data source ('tracker', 'nndss', or None for all)

    Returns:
        Disease-specific statistics including total cases, affected regions, and recent trends
    """
    try:
        disease_name = await get_disease_name_or_404(disease_slug)
        stats = await run_db_query(db.get_disease_stats, disease_name, data_source=data_source)

        return DiseaseStatsResponse(
            disease_name=disease_name,
            disease_slug=disease_slug,
            total_cases=stats["total_cases"],
            affected_states=stats["affected_states"],
            affected_counties=stats["affected_counties"],
            two_week_cases=stats["two_week_cases"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stats for {disease_slug}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch disease statistics") from e


@router.get("/disease/{disease_slug}/age-groups", response_model=AgeGroupDistributionResponse)
async def get_age_group_distribution(disease_slug: str, data_source: str | None = None):
    """
    Get age group distribution by state for a specific disease.

    Args:
        disease_slug: URL-safe slug for the disease
        data_source: Optional filter by data source ('tracker', 'nndss', or None for all)

    Returns:
        Age group distribution with percentages for each state
        Note: NNDSS data does not include age group information
    """
    try:
        disease_name = await get_disease_name_or_404(disease_slug)
        data = await run_db_query(db.get_age_group_distribution_by_state, disease_name, data_source=data_source)

        # Convert to proper format
        states_formatted = {}
        for state, age_data in data["states"].items():
            states_formatted[state] = {
                age_group: AgeGroupData(**values)
                for age_group, values in age_data.items()
            }

        return AgeGroupDistributionResponse(
            disease_name=disease_name,
            disease_slug=disease_slug,
            age_groups=data["age_groups"],
            available_states=data["available_states"],
            states=states_formatted
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching age group distribution for {disease_slug}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch age group distribution") from e
