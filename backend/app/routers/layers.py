from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.services.data_loader import data_loader
import json

router = APIRouter(prefix="/api/layers", tags=["layers"])

AVAILABLE_LAYERS = [
    "demographic",
    "roads",
    "poi",
    "land_use",
    "environmental",
    "competitor_locations",
]


@router.get("/")
async def list_layers():
    return {"layers": AVAILABLE_LAYERS}


@router.get("/{layer_name}")
async def get_layer(layer_name: str):
    if layer_name not in AVAILABLE_LAYERS:
        raise HTTPException(
            status_code=404, detail=f"Layer '{layer_name}' not found"
        )
    try:
        gdf = data_loader.load_layer(layer_name)
        return JSONResponse(content=json.loads(gdf.to_json()))
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
