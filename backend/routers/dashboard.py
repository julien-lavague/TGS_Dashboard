from fastapi import APIRouter

from services.gcp_status_service import get_gcp_status

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/gcp-status")
async def gcp_status(refresh: bool = False):
    return await get_gcp_status(force=refresh)
