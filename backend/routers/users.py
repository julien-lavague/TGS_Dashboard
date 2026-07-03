from fastapi import APIRouter
from schemas.users import UsersListResponse, AnonymousStatsResponse
from services.users_service import get_users_by_segment, get_anonymous_visitor_stats

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/list", response_model=UsersListResponse)
async def users_list():
    return UsersListResponse(segments=await get_users_by_segment())


@router.get("/anonymous-stats", response_model=AnonymousStatsResponse)
async def anonymous_stats():
    return AnonymousStatsResponse(**(await get_anonymous_visitor_stats()))
