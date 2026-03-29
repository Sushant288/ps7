from fastapi import APIRouter, Query, HTTPException
from app.services.clustering import generate_hotspot_analysis
from app.models.schemas import HotspotAnalysis, LayerWeights

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/hotspots", response_model=HotspotAnalysis)
async def get_hotspots(
    min_lng: float = Query(default=-122.5),
    min_lat: float = Query(default=37.7),
    max_lng: float = Query(default=-122.35),
    max_lat: float = Query(default=37.82),
    use_case: str = Query(default="retail"),
    h3_resolution: int = Query(default=8, ge=5, le=10),
):
    try:
        return generate_hotspot_analysis(
            bbox=(min_lng, min_lat, max_lng, max_lat),
            use_case=use_case,
            h3_resolution=h3_resolution,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
