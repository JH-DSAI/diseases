"""HTML fragment endpoints for HTMX"""

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.database import db
from app.dependencies import get_db, get_disease_name_or_404, run_db_query
from app.templates import templates

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/html",
    tags=["html"],
)


@router.get("/diseases", response_class=HTMLResponse)
async def get_disease_cards(
    request: Request, data_source: str | None = None, _db=Depends(get_db)
):
    """
    Returns HTML fragment containing all disease cards.
    Used by HTMX to populate the landing page grid.

    Args:
        data_source: Optional filter for data source (e.g., 'nndss', 'tracker')
    """
    diseases_raw = await run_db_query(db.get_diseases_with_slugs, data_source)

    # Get summary stats for cumulative totals (filtered by source if specified)
    stats = await run_db_query(db.get_summary_stats, data_source)
    disease_totals = {d["disease_name"]: d["total_cases"] for d in stats.get("disease_totals", [])}

    # Enrich diseases with total cases and data source
    diseases = []
    for d in diseases_raw:
        diseases.append({
            "name": d["name"],
            "slug": d["slug"],
            "total_cases": disease_totals.get(d["name"]),
            "data_source": d.get("data_source", ""),
        })

    return templates.TemplateResponse(
        request, "partials/disease_cards.html", {"diseases": diseases}
    )


@router.get("/disease/{disease_slug}/stats", response_class=HTMLResponse)
async def get_disease_stats(request: Request, disease_slug: str, _db=Depends(get_db)):
    """
    Returns HTML fragment containing disease statistics.
    Used by HTMX to populate the stats bar on disease detail page.
    """
    disease_name = await get_disease_name_or_404(disease_slug)
    stats_raw = await run_db_query(db.get_disease_stats, disease_name)

    stats = {
        "disease_name": disease_name,
        "disease_slug": disease_slug,
        "total_cases": stats_raw["total_cases"],
        "affected_states": stats_raw["affected_states"],
        "affected_counties": stats_raw["affected_counties"],
        "two_week_cases": stats_raw["two_week_cases"],
    }

    return templates.TemplateResponse(request, "partials/disease_stats.html", {"stats": stats})


@router.get("/disease/{disease_slug}/timeseries", response_class=HTMLResponse)
async def get_timeseries_chart(
    request: Request, disease_slug: str, granularity: str = "month", _db=Depends(get_db)
):
    """
    Returns HTML fragment containing time series chart with embedded data.
    Used by HTMX to populate the chart section on disease detail page.
    """
    disease_name = await get_disease_name_or_404(disease_slug)
    chart_data = await run_db_query(db.get_disease_timeseries_by_state, disease_name, granularity)

    return templates.TemplateResponse(
        request,
        "partials/timeseries_chart.html",
        {
            "disease_slug": disease_slug,
            "disease_name": disease_name,
            "granularity": granularity,
            "chart_data": chart_data,
        },
    )


@router.get("/disease/{disease_slug}/age-groups", response_class=HTMLResponse)
async def get_age_group_chart(request: Request, disease_slug: str, _db=Depends(get_db)):
    """
    Returns HTML fragment containing age group chart with embedded data.
    Used by HTMX to populate the chart section on disease detail page.
    """
    disease_name = await get_disease_name_or_404(disease_slug)
    chart_data = await run_db_query(db.get_age_group_distribution_by_state, disease_name)

    return templates.TemplateResponse(
        request,
        "partials/age_group_chart.html",
        {
            "disease_slug": disease_slug,
            "disease_name": disease_name,
            "chart_data": chart_data,
        },
    )


@router.get("/disease/{disease_slug}/serotypes", response_class=HTMLResponse)
async def get_serotype_chart(request: Request, disease_slug: str, _db=Depends(get_db)):
    """
    Returns HTML fragment containing serotype distribution chart with embedded data.
    Used by HTMX to populate the serotype section on meningococcal disease detail page.
    Only shows data for states that have serotype information.
    """
    disease_name = await get_disease_name_or_404(disease_slug)
    chart_data = await run_db_query(db.get_serotype_distribution_by_state, disease_name)

    return templates.TemplateResponse(
        request,
        "partials/serotype_chart.html",
        {
            "disease_slug": disease_slug,
            "disease_name": disease_name,
            "chart_data": chart_data,
        },
    )
