from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class LayerWeights(BaseModel):
    demographic: float = Field(default=0.2, ge=0.0, le=1.0)
    transportation: float = Field(default=0.2, ge=0.0, le=1.0)
    poi: float = Field(default=0.2, ge=0.0, le=1.0)
    land_use: float = Field(default=0.2, ge=0.0, le=1.0)
    environmental: float = Field(default=0.2, ge=0.0, le=1.0)


class ScoreRequest(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude of the site")
    lng: float = Field(..., ge=-180.0, le=180.0, description="Longitude of the site")
    use_case: str = Field(
        default="retail",
        description="Use case type: retail, warehouse, ev_charging, telecom, renewable"
    )
    weights: Optional[LayerWeights] = None
    radius_km: float = Field(default=1.0, ge=0.1, le=20.0)
    threshold_population: int = Field(default=5000, ge=0)


class ScoreBreakdown(BaseModel):
    layer_name: str
    score: float = Field(ge=0.0, le=100.0)
    weight: float = Field(ge=0.0, le=1.0)
    contribution: float
    factors: Dict[str, Any]


class SiteReadinessScore(BaseModel):
    lat: float
    lng: float
    composite_score: float = Field(ge=0.0, le=100.0)
    grade: str
    breakdowns: List[ScoreBreakdown]
    h3_index: str
    recommendations: List[str]


class H3Cell(BaseModel):
    h3_index: str
    score: float
    centroid_lat: float
    centroid_lng: float
    cluster_id: int


class Cluster(BaseModel):
    cluster_id: int
    centroid: List[float]
    size: int
    avg_score: float
    classification: str


class HotspotAnalysis(BaseModel):
    h3_cells: List[H3Cell]
    clusters: List[Cluster]


class Isochrone(BaseModel):
    minutes: int
    mode: str
    geojson_geometry: Dict[str, Any]
    population_within: int
    area_sqkm: float


class IsochroneResponse(BaseModel):
    site_lat: float
    site_lng: float
    isochrones: List[Isochrone]


class SiteComparison(BaseModel):
    sites: List[SiteReadinessScore]
    ranking: List[int]
    recommendation: str
