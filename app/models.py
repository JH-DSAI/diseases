"""Pydantic models for API responses"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    database_initialized: bool = Field(..., description="Database initialization status")


class DiseaseListItem(BaseModel):
    """Disease list item model"""
    name: str = Field(..., description="Disease name")


class DiseaseListResponse(BaseModel):
    """Disease list response model"""
    diseases: list[DiseaseListItem] = Field(..., description="List of diseases")
    count: int = Field(..., description="Total number of diseases")


class SummaryStatsResponse(BaseModel):
    """Summary statistics response model"""
    total_records: int = Field(0, description="Total number of records")
    total_diseases: int = Field(0, description="Total number of unique diseases")
    total_states: int = Field(0, description="Total number of states")
    total_cases: int = Field(0, description="Total case count")
    earliest_date: str | None = Field(None, description="Earliest report date")
    latest_date: str | None = Field(None, description="Latest report date")


class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(..., description="Error detail message")
