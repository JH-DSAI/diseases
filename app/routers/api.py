"""JSON API endpoints"""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth import verify_api_key
from app.config import settings
from app.database import db
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
    prefix="/api",
    tags=["api"],
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
        database_initialized=db._initialized
    )


@router.get("/diseases", response_model=DiseaseListResponse)
async def list_diseases(data_source: str | None = None):
    """
    Get list of all diseases tracked in the database.

    Args:
        data_source: Optional filter by data source ('tracker', 'nndss', or None for all)

    Returns:
        List of disease names
    """
    try:
        diseases = await asyncio.to_thread(db.get_diseases, data_source=data_source)
        return DiseaseListResponse(
            diseases=[DiseaseListItem(name=d) for d in diseases],
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
        stats = await asyncio.to_thread(db.get_summary_stats, data_source=data_source)
        return SummaryStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics") from e


@router.get("/timeseries/national/{disease_name}", response_model=NationalDiseaseTimeSeriesResponse)
async def get_national_disease_timeseries(disease_name: str, granularity: str = 'month',
                                         data_source: str | None = None):
    """
    Get national time series data for a specific disease.

    Args:
        disease_name: Name of the disease
        granularity: Time granularity ('month' or 'week'), defaults to 'month'
        data_source: Optional filter by data source ('tracker', 'nndss', or None for all)

    Returns:
        Time series data points with period and total national cases
    """
    try:
        # Verify disease exists
        diseases = await asyncio.to_thread(db.get_diseases, data_source=data_source)
        if disease_name not in diseases:
            raise HTTPException(status_code=404, detail=f"Disease '{disease_name}' not found")

        # Get time series data
        data = await asyncio.to_thread(db.get_national_disease_timeseries, disease_name, granularity, data_source=data_source)

        return NationalDiseaseTimeSeriesResponse(
            disease_name=disease_name,
            granularity=granularity,
            data=[NationalDiseaseTimeSeriesDataPoint(**point) for point in data]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching timeseries for {disease_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch time series data") from e


@router.get("/timeseries/states/{disease_name}", response_model=DiseaseTimeSeriesByStateResponse)
async def get_disease_timeseries_by_state(disease_name: str, granularity: str = 'month',
                                         data_source: str | None = None):
    """
    Get state-level time series data for a specific disease.

    Args:
        disease_name: Name of the disease
        granularity: Time granularity ('month' or 'week'), defaults to 'month'
        data_source: Optional filter by data source ('tracker', 'nndss', or None for all)

    Returns:
        Time series data broken down by state plus national total
    """
    try:
        # Verify disease exists
        diseases = await asyncio.to_thread(db.get_diseases, data_source=data_source)
        if disease_name not in diseases:
            raise HTTPException(status_code=404, detail=f"Disease '{disease_name}' not found")

        # Get time series data
        data = await asyncio.to_thread(db.get_disease_timeseries_by_state, disease_name, granularity, data_source=data_source)

        # Convert states data to proper format
        states_formatted = {}
        for state, state_data in data["states"].items():
            states_formatted[state] = [StateTimeSeriesDataPoint(**point) for point in state_data]

        # Convert national data to proper format
        national_formatted = [StateTimeSeriesDataPoint(**point) for point in data["national"]]

        return DiseaseTimeSeriesByStateResponse(
            disease_name=disease_name,
            granularity=granularity,
            available_states=data["available_states"],
            states=states_formatted,
            national=national_formatted
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching state timeseries for {disease_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch state time series data") from e


@router.get("/disease/{disease_name}/stats", response_model=DiseaseStatsResponse)
async def get_disease_stats(disease_name: str, data_source: str | None = None):
    """
    Get summary statistics for a specific disease.

    Args:
        disease_name: Name of the disease
        data_source: Optional filter by data source ('tracker', 'nndss', or None for all)

    Returns:
        Disease-specific statistics including total cases, affected regions, and recent trends
    """
    try:
        # Verify disease exists
        diseases = await asyncio.to_thread(db.get_diseases, data_source=data_source)
        if disease_name not in diseases:
            raise HTTPException(status_code=404, detail=f"Disease '{disease_name}' not found")

        # Get disease stats
        stats = await asyncio.to_thread(db.get_disease_stats, disease_name, data_source=data_source)

        return DiseaseStatsResponse(
            disease_name=disease_name,
            total_cases=stats["total_cases"],
            affected_states=stats["affected_states"],
            affected_counties=stats["affected_counties"],
            two_week_cases=stats["two_week_cases"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stats for {disease_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch disease statistics") from e


@router.get("/disease/{disease_name}/age-groups", response_model=AgeGroupDistributionResponse)
async def get_age_group_distribution(disease_name: str, data_source: str | None = None):
    """
    Get age group distribution by state for a specific disease.

    Args:
        disease_name: Name of the disease
        data_source: Optional filter by data source ('tracker', 'nndss', or None for all)

    Returns:
        Age group distribution with percentages for each state
        Note: NNDSS data does not include age group information
    """
    try:
        # Verify disease exists
        diseases = await asyncio.to_thread(db.get_diseases, data_source=data_source)
        if disease_name not in diseases:
            raise HTTPException(status_code=404, detail=f"Disease '{disease_name}' not found")

        # Get age group distribution
        data = await asyncio.to_thread(db.get_age_group_distribution_by_state, disease_name, data_source=data_source)

        # Convert to proper format
        states_formatted = {}
        for state, age_data in data["states"].items():
            states_formatted[state] = {
                age_group: AgeGroupData(**values)
                for age_group, values in age_data.items()
            }

        return AgeGroupDistributionResponse(
            disease_name=disease_name,
            age_groups=data["age_groups"],
            available_states=data["available_states"],
            states=states_formatted
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching age group distribution for {disease_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch age group distribution") from e
