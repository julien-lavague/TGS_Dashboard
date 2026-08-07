from fastapi import APIRouter, Query
from schemas.usage import FigureResponse
from services.profils_service import get_spot_distribution_figure, get_level_by_sport_figure, get_spots_per_profile_figure, get_spots_per_profile_detail, get_profile_characteristics, get_user_profiles, get_spot_map_figure

router = APIRouter(prefix="/api/profils", tags=["profils"])


@router.get("/spot-distribution", response_model=FigureResponse)
async def spot_distribution(segment: str = Query("release")):
    return FigureResponse(figure=await get_spot_distribution_figure(segment))


@router.get("/spot-map", response_model=FigureResponse)
async def spot_map(segment: str = Query("release")):
    return FigureResponse(figure=await get_spot_map_figure(segment))


@router.get("/level-by-sport", response_model=FigureResponse)
async def level_by_sport(segment: str = Query("release")):
    return FigureResponse(figure=await get_level_by_sport_figure(segment))


@router.get("/spots-per-profile", response_model=FigureResponse)
async def spots_per_profile(segment: str = Query("release")):
    return FigureResponse(figure=await get_spots_per_profile_figure(segment))


@router.get("/spots-per-profile-detail")
async def spots_per_profile_detail(segment: str = Query("release")):
    return await get_spots_per_profile_detail(segment)


@router.get("/characteristics")
async def profile_characteristics(segment: str = Query("release"), group_by: str = Query("sport")):
    return await get_profile_characteristics(segment, group_by)


@router.get("/user-profiles")
async def user_profiles(segment: str = Query("release")):
    return await get_user_profiles(segment)
