from fastapi import APIRouter
from schemas.users import UsersListResponse
from services.users_service import get_users_by_segment

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/list", response_model=UsersListResponse)
async def users_list():
    return UsersListResponse(segments=await get_users_by_segment())
