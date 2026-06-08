from fastapi import APIRouter, Query
from schemas.usage import FigureResponse
from services.usage_service import get_page_views_figure, get_sessions_figure, get_sessions_per_week_since_signup_figure, get_timeline_figure

router = APIRouter(prefix="/api/usage", tags=["usage"])


@router.get("/page-views", response_model=FigureResponse)
async def page_views(segment: str = Query("release")):
    return FigureResponse(figure=await get_page_views_figure(segment))


@router.get("/sessions", response_model=FigureResponse)
async def sessions(segment: str = Query("release")):
    return FigureResponse(figure=await get_sessions_figure(segment))


@router.get("/sessions-per-week-since-signup", response_model=FigureResponse)
async def sessions_per_week_since_signup(segment: str = Query("release")):
    return FigureResponse(figure=await get_sessions_per_week_since_signup_figure(segment))


@router.get("/timeline", response_model=FigureResponse)
async def timeline(segment: str = Query("release")):
    return FigureResponse(figure=await get_timeline_figure(segment))
