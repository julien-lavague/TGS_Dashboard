from fastapi import APIRouter, Query
from schemas.usage import FigureResponse
from services.profils_service import get_spot_distribution_figure, get_level_by_sport_figure, get_spots_per_profile_figure, get_spots_per_profile_detail

router = APIRouter(prefix="/api/profils", tags=["profils"])


@router.get("/spot-distribution", response_model=FigureResponse)
async def spot_distribution(segment: str = Query("release")):
    return FigureResponse(figure=await get_spot_distribution_figure(segment))


@router.get("/level-by-sport", response_model=FigureResponse)
async def level_by_sport(segment: str = Query("release")):
    return FigureResponse(figure=await get_level_by_sport_figure(segment))


@router.get("/spots-per-profile", response_model=FigureResponse)
async def spots_per_profile(segment: str = Query("release")):
    return FigureResponse(figure=await get_spots_per_profile_figure(segment))


@router.get("/spots-per-profile-detail")
async def spots_per_profile_detail(segment: str = Query("release")):
    return await get_spots_per_profile_detail(segment)
