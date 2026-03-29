from fastapi import APIRouter, Query, HTTPException
from app.services.isochrone_service import compute_isochrone

router = APIRouter(prefix="/api/isochrone", tags=["isochrone"])


@router.get("/")
async def get_isochrone(
    lat: float = Query(..., description="Site latitude"),
    lng: float = Query(..., description="Site longitude"),
    mode: str = Query(default="drive", description="Travel mode: drive, walk, transit"),
    minutes: str = Query(default="10,20,30", description="Comma-separated minutes list"),
):
    try:
        minutes_list = [int(m.strip()) for m in minutes.split(",") if m.strip().isdigit()]
        if not minutes_list:
            minutes_list = [10, 20, 30]
        minutes_list = [m for m in minutes_list if 1 <= m <= 120]

        isochrones = compute_isochrone(lat, lng, minutes_list, mode)
        return {"lat": lat, "lng": lng, "isochrones": isochrones}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
