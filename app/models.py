"""Pydantic models for API responses"""

from datetime import datetime

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


class DiseaseTotalItem(BaseModel):
    """Disease total item model"""
    disease_name: str = Field(..., description="Disease name")
    total_cases: int = Field(..., description="Total cases nationally (across all states)")


class SummaryStatsResponse(BaseModel):
    """Summary statistics response model"""
    total_records: int = Field(0, description="Total number of records")
    total_diseases: int = Field(0, description="Total number of unique diseases")
    total_states: int = Field(0, description="Total number of states")
    total_cases: int = Field(0, description="Total case count")
    earliest_date: datetime | None = Field(None, description="Earliest report date")
    latest_date: datetime | None = Field(None, description="Latest report date")
    disease_totals: list[DiseaseTotalItem] = Field(default_factory=list, description="National totals for each disease")


class NationalDiseaseTimeSeriesDataPoint(BaseModel):
    """National disease time series data point model"""
    period: str = Field(..., description="Time period (YYYY-MM-DD format)")
    total_cases: int = Field(..., description="Total cases nationally for this period")


class NationalDiseaseTimeSeriesResponse(BaseModel):
    """National disease time series response model"""
    disease_name: str = Field(..., description="Disease name")
    granularity: str = Field(..., description="Time granularity (month or week)")
    data: list[NationalDiseaseTimeSeriesDataPoint] = Field(..., description="Time series data points")


class StateTimeSeriesDataPoint(BaseModel):
    """State-level time series data point model"""
    period: str = Field(..., description="Time period (YYYY-MM-DD format)")
    cases: int = Field(..., description="Cases for this state in this period")


class StateTimeSeriesData(BaseModel):
    """State-level time series data model"""
    state: str = Field(..., description="State name")
    data: list[StateTimeSeriesDataPoint] = Field(..., description="Time series data points for this state")


class DiseaseTimeSeriesByStateResponse(BaseModel):
    """Disease time series by state response model"""
    disease_name: str = Field(..., description="Disease name")
    granularity: str = Field(..., description="Time granularity (month or week)")
    available_states: list[str] = Field(..., description="List of states with data for this disease")
    states: dict[str, list[StateTimeSeriesDataPoint]] = Field(..., description="Time series data by state")
    national: list[StateTimeSeriesDataPoint] = Field(..., description="National total time series data")


class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(..., description="Error detail message")
