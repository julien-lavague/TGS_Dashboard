from fastapi import APIRouter, Query
from schemas.usage import FigureResponse
from services.equipments_service import get_equipment_coverage_figure, get_equipment_by_type_figure, get_equipment_names, get_equipment_characteristics

router = APIRouter(prefix="/api/equipments", tags=["equipments"])


@router.get("/coverage", response_model=FigureResponse)
async def equipment_coverage(segment: str = Query("all")):
    return FigureResponse(figure=await get_equipment_coverage_figure(segment))


@router.get("/by-type", response_model=FigureResponse)
async def equipment_by_type(segment: str = Query("all")):
    return FigureResponse(figure=await get_equipment_by_type_figure(segment))


@router.get("/names")
async def equipment_names(segment: str = Query("all")):
    return await get_equipment_names(segment)


@router.get("/characteristics")
async def equipment_characteristics(segment: str = Query("all")):
    return await get_equipment_characteristics(segment)
