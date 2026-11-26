from fastapi import APIRouter

from services.gcp_status_service import get_gcp_status
from services.pending_poi_service import get_pending_poi

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/gcp-status")
async def gcp_status(refresh: bool = False):
    return await get_gcp_status(force=refresh)


@router.get("/pending-poi")
async def pending_poi():
    return await get_pending_poi()
