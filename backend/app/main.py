from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import score, layers, analysis, isochrone, export
from app.routers import ai_analysis

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "AI-Powered GeoSpatial Site Readiness Analyzer for the SF Bay Area. "
        "Score any location across demographic, transportation, POI, land-use, "
        "and environmental dimensions."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(score.router)
app.include_router(layers.router)
app.include_router(analysis.router)
app.include_router(isochrone.router)
app.include_router(export.router)
app.include_router(ai_analysis.router)


@app.get("/", tags=["root"])
async def root():
    return {
        "message": "GeoSpatial Site Readiness Analyzer API",
        "version": "1.0.0",
        "docs": "/docs",
        "demo_area": "San Francisco Bay Area",
        "bbox": {
            "min_lng": -122.5,
            "min_lat": 37.7,
            "max_lng": -122.35,
            "max_lat": 37.82,
        },
    }


@app.get("/health", tags=["root"])
async def health():
    return {"status": "healthy"}
