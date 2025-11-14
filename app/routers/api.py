"""JSON API endpoints"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth import verify_api_key
from app.config import settings
from app.database import db
from app.models import (
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
async def list_diseases():
    """
    Get list of all diseases tracked in the database.

    Returns:
        List of disease names
    """
    try:
        diseases = db.get_diseases()
        return DiseaseListResponse(
            diseases=[DiseaseListItem(name=d) for d in diseases],
            count=len(diseases)
        )
    except Exception as e:
        logger.error(f"Error fetching diseases: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch diseases") from e


@router.get("/stats", response_model=SummaryStatsResponse)
async def get_summary_stats():
    """
    Get summary statistics across all disease data.

    Returns:
        Summary statistics including total cases, date ranges, etc.
    """
    try:
        stats = db.get_summary_stats()
        return SummaryStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics") from e


@router.get("/timeseries/national/{disease_name}", response_model=NationalDiseaseTimeSeriesResponse)
async def get_national_disease_timeseries(disease_name: str, granularity: str = 'month'):
    """
    Get national time series data for a specific disease.

    Args:
        disease_name: Name of the disease
        granularity: Time granularity ('month' or 'week'), defaults to 'month'

    Returns:
        Time series data points with period and total national cases
    """
    try:
        # Verify disease exists
        diseases = db.get_diseases()
        if disease_name not in diseases:
            raise HTTPException(status_code=404, detail=f"Disease '{disease_name}' not found")

        # Get time series data
        data = db.get_national_disease_timeseries(disease_name, granularity)

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
async def get_disease_timeseries_by_state(disease_name: str, granularity: str = 'month'):
    """
    Get state-level time series data for a specific disease.

    Args:
        disease_name: Name of the disease
        granularity: Time granularity ('month' or 'week'), defaults to 'month'

    Returns:
        Time series data broken down by state plus national total
    """
    try:
        # Verify disease exists
        diseases = db.get_diseases()
        if disease_name not in diseases:
            raise HTTPException(status_code=404, detail=f"Disease '{disease_name}' not found")

        # Get time series data
        data = db.get_disease_timeseries_by_state(disease_name, granularity)

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
async def get_disease_stats(disease_name: str):
    """
    Get summary statistics for a specific disease.

    Args:
        disease_name: Name of the disease

    Returns:
        Disease-specific statistics including total cases, affected regions, and recent trends
    """
    try:
        # Verify disease exists
        diseases = db.get_diseases()
        if disease_name not in diseases:
            raise HTTPException(status_code=404, detail=f"Disease '{disease_name}' not found")

        # Get disease stats
        stats = db.get_disease_stats(disease_name)

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
