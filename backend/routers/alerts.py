from fastapi import APIRouter, Query
from schemas.alerts import AlertsResponse
from services.alerts_service import get_alert_schedule

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/schedule", response_model=AlertsResponse)
async def alerts_schedule(segment: str = Query("release")):
    rows = await get_alert_schedule(segment)
    return AlertsResponse(rows=rows)
