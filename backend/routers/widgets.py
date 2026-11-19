from typing import Literal, Optional
from fastapi import APIRouter, Query
from schemas.usage import FigureResponse
from services.widgets_service import (
    get_cell_clicks_figure,
    get_element_usage_figure,
    get_filters_figure,
    get_paywall_funnel_figure,
    get_timeline_depth_figure,
)

Site = Literal["prod", "dev"]

router = APIRouter(prefix="/api/widgets", tags=["widgets"])


@router.get("/element-usage", response_model=FigureResponse)
async def element_usage(segment: str = Query("release"), days: Optional[int] = Query(None), site: Site = Query("prod")):
    return FigureResponse(figure=await get_element_usage_figure(segment, days, site))


@router.get("/timeline-depth", response_model=FigureResponse)
async def timeline_depth(segment: str = Query("release"), days: Optional[int] = Query(None), site: Site = Query("prod")):
    return FigureResponse(figure=await get_timeline_depth_figure(segment, days, site))


@router.get("/cell-clicks", response_model=FigureResponse)
async def cell_clicks(segment: str = Query("release"), days: Optional[int] = Query(None), site: Site = Query("prod")):
    return FigureResponse(figure=await get_cell_clicks_figure(segment, days, site))


@router.get("/filters", response_model=FigureResponse)
async def filters(segment: str = Query("release"), days: Optional[int] = Query(None), site: Site = Query("prod")):
    return FigureResponse(figure=await get_filters_figure(segment, days, site))


@router.get("/paywall-funnel", response_model=FigureResponse)
async def paywall_funnel(segment: str = Query("release"), days: Optional[int] = Query(None), site: Site = Query("prod")):
    return FigureResponse(figure=await get_paywall_funnel_figure(segment, days, site))
