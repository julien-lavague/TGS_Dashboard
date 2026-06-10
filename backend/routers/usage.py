from typing import Optional
from fastapi import APIRouter, Query
from schemas.usage import FigureResponse
from services.usage_service import get_page_views_figure, get_sessions_figure, get_sessions_per_week_since_signup_figure, get_timeline_figure, get_visit_duration_figure, get_daily_active_users_figure, get_user_visits_pareto_figure, get_visit_frequency_figure

router = APIRouter(prefix="/api/usage", tags=["usage"])


@router.get("/page-views", response_model=FigureResponse)
async def page_views(segment: str = Query("release"), days: Optional[int] = Query(None)):
    return FigureResponse(figure=await get_page_views_figure(segment, days))


@router.get("/sessions", response_model=FigureResponse)
async def sessions(segment: str = Query("release"), days: Optional[int] = Query(None)):
    return FigureResponse(figure=await get_sessions_figure(segment, days))


@router.get("/sessions-per-week-since-signup", response_model=FigureResponse)
async def sessions_per_week_since_signup(segment: str = Query("release"), days: Optional[int] = Query(None)):
    return FigureResponse(figure=await get_sessions_per_week_since_signup_figure(segment, days))


@router.get("/timeline", response_model=FigureResponse)
async def timeline(segment: str = Query("release"), days: Optional[int] = Query(None)):
    return FigureResponse(figure=await get_timeline_figure(segment, days))


@router.get("/visit-duration", response_model=FigureResponse)
async def visit_duration(segment: str = Query("release"), days: Optional[int] = Query(None)):
    return FigureResponse(figure=await get_visit_duration_figure(segment, days))


@router.get("/daily-active-users", response_model=FigureResponse)
async def daily_active_users(segment: str = Query("release"), days: Optional[int] = Query(None)):
    return FigureResponse(figure=await get_daily_active_users_figure(segment, days))


@router.get("/user-visits-pareto", response_model=FigureResponse)
async def user_visits_pareto(segment: str = Query("release"), days: Optional[int] = Query(None)):
    return FigureResponse(figure=await get_user_visits_pareto_figure(segment, days))


@router.get("/visit-frequency", response_model=FigureResponse)
async def visit_frequency(segment: str = Query("release"), days: Optional[int] = Query(None)):
    return FigureResponse(figure=await get_visit_frequency_figure(segment, days))
