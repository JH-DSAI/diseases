"""JSON API endpoints"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth import verify_api_key
from app.config import settings
from app.database import db
from app.models import (
    DiseaseListItem,
    DiseaseListResponse,
    HealthResponse,
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
