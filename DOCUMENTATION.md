# GeoSpatial Site Readiness Analyzer
## Complete Technical & User Documentation
### Hackathon Submission — AI-Powered Location Intelligence for Commercial Real Estate & Infrastructure

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Directory Structure](#3-directory-structure)
4. [Setup & Running](#4-setup--running)
5. [Data Layer System](#5-data-layer-system)
6. [Scoring Engine — Deep Dive](#6-scoring-engine--deep-dive)
7. [Spatial Analysis — Hotspots & Clustering](#7-spatial-analysis--hotspots--clustering)
8. [Isochrone & Accessibility Analysis](#8-isochrone--accessibility-analysis)
9. [REST API Reference](#9-rest-api-reference)
10. [Frontend — UI Walkthrough](#10-frontend--ui-walkthrough)
11. [Component Reference](#11-component-reference)
12. [Use Case Presets](#12-use-case-presets)
13. [Export System](#13-export-system)
14. [Evaluation Criteria Mapping](#14-evaluation-criteria-mapping)

---

## 1. Project Overview

The GeoSpatial Site Readiness Analyzer is a full-stack AI-powered web application that scores any geographic location (latitude/longitude) on a 0–100 scale for suitability as a commercial or infrastructure site. It ingests 6 geospatial data layers, runs a configurable multi-factor scoring model, performs spatial clustering to identify city-wide hotspots, and computes drive/walk/transit catchment areas — all visualized on an interactive dark-mode map.

**Demo Area:** San Francisco Bay Area (bbox: -122.5°W to -122.35°W, 37.7°N to 37.82°N)

**Tech Stack:**
- Backend: Python 3.13, FastAPI, GeoPandas, Shapely, H3, scikit-learn, SciPy
- Frontend: React 18, Vite, Leaflet, Recharts, Tailwind CSS
- Data Format: GeoJSON (all layers)
- Projection: WGS84 (EPSG:4326) storage, UTM Zone 10N (EPSG:32610) for distance calculations

---

## 2. Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        BROWSER (port 5173)                     │
│  ┌──────────────┐  ┌────────────┐  ┌────────────────────────┐  │
│  │  Left Sidebar │  │  Leaflet   │  │   Right Score Panel    │  │
│  │  - Use Case  │  │  Map       │  │   - Score circle       │  │
│  │  - Weights   │  │  - Layers  │  │   - Radar chart        │  │
│  │  - Layers    │  │  - Hexes   │  │   - Layer drilldown    │  │
│  │  - Tools     │  │  - Isos    │  │   - Recommendations    │  │
│  └──────────────┘  └────────────┘  └────────────────────────┘  │
│                    ┌──────────────────────────────────────────┐ │
│                    │  Bottom: Site Comparison Bar              │ │
│                    └──────────────────────────────────────────┘ │
└──────────────────────────────┬─────────────────────────────────┘
                               │ HTTP (proxied /api → :8000)
┌──────────────────────────────▼─────────────────────────────────┐
│                    FastAPI Backend (port 8000)                  │
│                                                                 │
│  /api/score/site ──► ScoringEngine ──► 5 layer scorers         │
│  /api/score/compare ──► ranked comparison                      │
│  /api/layers/{name} ──► GeoJSON layer serving                  │
│  /api/analysis/hotspots ──► H3 binning + DBSCAN                │
│  /api/isochrone/ ──► road-adjusted catchment polygons          │
│  /api/export/json|csv ──► downloadable reports                 │
│                                                                 │
│  DataLoader (in-memory cache)                                   │
│  ┌──────────┬──────────┬────────┬──────────┬──────────────────┐│
│  │ demo-    │ roads.   │ poi.   │land_use. │ environmental.   ││
│  │ graphic  │ geojson  │ geojson│ geojson  │ geojson          ││
│  └──────────┴──────────┴────────┴──────────┴──────────────────┘│
└────────────────────────────────────────────────────────────────┘
```

**Request flow for a single site score:**
1. User clicks map → React sends `POST /api/score/site` with `{lat, lng, use_case, weights}`
2. FastAPI routes to `compute_site_score()`
3. Each of 5 layer scorers loads its GeoDataFrame (cached), reprojects to UTM, computes distances, returns a 0–100 score + factor dict
4. Weights are normalized, weighted average computed, H3 index assigned
5. Response JSON returned → React renders ScorePanel with radar chart + breakdowns

---

## 3. Directory Structure

```
stmt7/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, CORS, router mounts
│   │   ├── config.py            # Pydantic settings (data_dir, CORS origins)
│   │   ├── routers/
│   │   │   ├── score.py         # POST /api/score/site, /api/score/compare
│   │   │   ├── layers.py        # GET /api/layers/, /api/layers/{name}
│   │   │   ├── analysis.py      # GET /api/analysis/hotspots
│   │   │   ├── isochrone.py     # GET /api/isochrone/
│   │   │   └── export.py        # POST /api/export/json, /api/export/csv
│   │   ├── services/
│   │   │   ├── data_loader.py   # DataLoader class with in-memory GDF cache
│   │   │   ├── scoring.py       # All 5 layer scoring functions + composite
│   │   │   ├── clustering.py    # H3 binning + DBSCAN hotspot analysis
│   │   │   └── isochrone_service.py  # Road-network-adjusted isochrones
│   │   └── models/
│   │       └── schemas.py       # All Pydantic request/response models
│   ├── data/                    # Auto-generated GeoJSON files
│   │   ├── demographic.geojson
│   │   ├── roads.geojson
│   │   ├── poi.geojson
│   │   ├── land_use.geojson
│   │   ├── environmental.geojson
│   │   └── competitor_locations.geojson
│   ├── generate_data.py         # Synthetic data generator (run once)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html               # Entry point, Leaflet CSS links
│   ├── vite.config.js           # Vite config, /api proxy to :8000
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── package.json
│   └── src/
│       ├── main.jsx             # React root mount
│       ├── App.jsx              # Root component, all state management
│       ├── index.css            # Tailwind + custom map styles
│       ├── components/
│       │   ├── Map.jsx          # Leaflet map, all layer rendering
│       │   ├── LayerPanel.jsx   # Layer toggle sidebar section
│       │   ├── ScorePanel.jsx   # Score breakdown right panel
│       │   ├── SiteComparison.jsx  # Bottom pinned sites bar
│       │   ├── HotspotLegend.jsx   # Score color legend overlay
│       │   └── ExportModal.jsx  # Export UI
│       └── utils/
│           └── api.js           # Axios wrappers for all API calls
├── docker-compose.yml
└── DOCUMENTATION.md             # This file
```

---

## 4. Setup & Running

### Prerequisites
- Python 3.11+ with pip
- Node.js 18+

### Step 1 — Generate Data (first time only)
```bash
cd /home/manan/stmt7/backend
python3 generate_data.py
```
Output:
```
✓ demographic.geojson: 50 features
✓ roads.geojson: 200 features
✓ poi.geojson: 300 features
✓ land_use.geojson: 80 features
✓ environmental.geojson: 60 features
✓ competitor_locations.geojson: 100 features
```

### Step 2 — Start Backend
```bash
cd /home/manan/stmt7/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API available at: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

### Step 3 — Start Frontend
```bash
cd /home/manan/stmt7/frontend
npm install
npm run dev
```
App available at: `http://localhost:5173`

### Docker (Alternative)
```bash
cd /home/manan/stmt7
docker-compose up --build
```

### Install Backend Dependencies
```bash
pip install fastapi uvicorn[standard] geopandas h3 scikit-learn pandas scipy \
            pyproj requests python-multipart aiofiles pydantic pydantic-settings \
            openpyxl fiona rtree --break-system-packages
```

---

## 5. Data Layer System

### Overview

All data is stored as GeoJSON files in `backend/data/`. The `DataLoader` class loads each file once and caches it as a GeoPandas GeoDataFrame in memory for fast repeated access.

```python
# backend/app/services/data_loader.py
class DataLoader:
    _cache = {}  # class-level cache, persists across requests

    @classmethod
    def load_layer(cls, layer_name: str) -> gpd.GeoDataFrame:
        if layer_name not in cls._cache:
            path = Path(settings.data_dir) / f"{layer_name}.geojson"
            gdf = gpd.read_file(path)
            if gdf.crs is None:
                gdf = gdf.set_crs(epsg=4326)
            cls._cache[layer_name] = gdf
        return cls._cache[layer_name]
```

**Why caching matters:** GeoPandas reads GeoJSON from disk on first call (~50–200ms). Subsequent calls return the cached GDF instantly. For hotspot analysis scoring 200+ hexagons, this is critical.

### Layer 1: Demographic (50 polygon features)

**File:** `demographic.geojson`
**Geometry:** Polygon (census tract approximations)
**Properties:**

| Field | Type | Range | Description |
|---|---|---|---|
| `population_density` | float | 100–15,000 /km² | Persons per square kilometer |
| `median_income` | float | $30,000–$200,000 | Household median income |
| `median_age` | float | 25–55 years | Median resident age |
| `population_total` | int | 1,000–50,000 | Total residents in tract |

**Generation logic:** 7×8 grid covering the SF bbox, each cell is a slightly irregularly shaped polygon. Downtown/SoMa gets higher density and income biasing.

**Map visualization:** Choropleth — green (high density) to red (low density), 40% opacity fill.

---

### Layer 2: Roads (200 LineString features)

**File:** `roads.geojson`
**Geometry:** LineString
**Properties:**

| Field | Type | Values | Description |
|---|---|---|---|
| `road_type` | string | highway / arterial / local | Road classification |
| `name` | string | — | Road name |
| `lanes` | int | 1–6 | Number of lanes |

**Generation logic:**
- 15 highway segments approximating US-101, I-280, I-80 corridors
- 40 arterial roads (major city streets)
- 145 local streets (random distribution)

**Map visualization:**
- Highways: amber (#f59e0b), weight 3px
- Arterials: blue (#60a5fa), weight 2px
- Local: slate (#94a3b8), weight 1px

---

### Layer 3: POI — Points of Interest (300 Point features)

**File:** `poi.geojson`
**Geometry:** Point
**Properties:**

| Field | Type | Values | Description |
|---|---|---|---|
| `category` | string | retail/restaurant/cafe/grocery/gym/pharmacy/competitor_* | Business type |
| `name` | string | — | Business name |
| `rating` | float | 3.0–5.0 | Customer rating |

**Generation logic:** 80% of POIs are biased toward 3 district centers (Downtown/FiDi, SoMa, Mission District). 20% random.

**Map visualization:** Colored circles by category (purple=retail, orange=restaurant, lime=cafe, cyan=grocery, pink=gym, emerald=pharmacy).

---

### Layer 4: Land Use / Zoning (80 Polygon features)

**File:** `land_use.geojson`
**Geometry:** Polygon
**Properties:**

| Field | Type | Values | Description |
|---|---|---|---|
| `zone_type` | string | commercial/residential/industrial/mixed/park/institutional | Zoning classification |
| `area_sqm` | float | — | Polygon area in square meters |

**Generation logic:** Irregular polygons distributed across the bbox. Commercial zones clustered near Market St / downtown. Industrial zones near SoMa/Potrero.

**Map visualization:** Fill colors — blue=commercial, green=residential, amber=industrial, purple=mixed, emerald=park, slate=institutional. 35% opacity.

---

### Layer 5: Environmental Risk (60 Polygon features)

**File:** `environmental.geojson`
**Geometry:** Polygon
**Properties:**

| Field | Type | Values | Description |
|---|---|---|---|
| `risk_type` | string | flood_zone/low_flood/earthquake_high/earthquake_medium/air_quality_good/moderate/poor | Risk category |
| `severity` | float | 0.0–1.0 | Risk severity multiplier |

**Map visualization:** Fill colors by risk — blue=flood, red=earthquake, purple=air quality. 35% opacity.

---

### Layer 6: Competitor Locations (100 Point features)

**File:** `competitor_locations.geojson`
**Geometry:** Point
**Properties:**

| Field | Type | Description |
|---|---|---|
| `business_type` | string | Type of competing business |
| `name` | string | Business name |
| `revenue_estimate` | float | Estimated annual revenue |

**Map visualization:** Red circles (#ef4444), slightly larger than POI markers to stand out.

---

## 6. Scoring Engine — Deep Dive

### Entry Point

All scoring starts at `compute_site_score()` in `backend/app/services/scoring.py`:

```python
def compute_site_score(req: ScoreRequest) -> SiteReadinessScore:
    weights = req.weights or LayerWeights()
    w = weights.dict()
    total_w = sum(w.values())  # normalize so weights always sum to 1

    layers = [
        ("demographic",    score_demographic(req.lat, req.lng, req.radius_km, req.threshold_population)),
        ("transportation",  score_transportation(req.lat, req.lng, req.radius_km)),
        ("poi",            score_poi(req.lat, req.lng, req.radius_km)),
        ("land_use",       score_land_use(req.lat, req.lng, req.radius_km)),
        ("environmental",  score_environmental(req.lat, req.lng, req.radius_km)),
    ]

    composite = sum(score * (weight / total_w) for (name, (score, _)) in layers for weight in [w[name]])
```

### Coordinate Projection

All distance calculations use UTM Zone 10N (EPSG:32610) — a metric CRS accurate for the SF Bay Area. Coordinates are stored in WGS84 (EPSG:4326) but reprojected per request:

```python
gdf_proj = gdf.to_crs(epsg=32610)
point_proj = gpd.GeoSeries([point], crs=4326).to_crs(epsg=32610).iloc[0]
distance_meters = gdf_proj.geometry.distance(point_proj)
```

This gives accurate meter-based distances instead of degree-based approximations.

---

### Distance Decay Functions

Three decay models are implemented. All return a 0–1 multiplier:

```python
def distance_decay(distance_km, decay_type="inverse", max_dist_km=5.0):
    if distance_km >= max_dist_km:
        return 0.0
    ratio = distance_km / max_dist_km

    if decay_type == "inverse":
        return 1.0 / (1.0 + distance_km * 2)    # Rapid early drop-off

    elif decay_type == "gaussian":
        return exp(-0.5 * (ratio * 3) ** 2)      # Bell curve, soft edges

    elif decay_type == "linear":
        return 1.0 - ratio                        # Constant decay rate
```

| Function | Shape | Used For |
|---|---|---|
| `gaussian` | Bell curve | Highway proximity (sharp benefit nearby, fades smoothly) |
| `linear` | Straight line | Arterial roads (constant decay) |
| `inverse` | Hyperbolic | General proximity (fast initial drop) |

**Example — Highway at 0.5km vs 3km:**
- Gaussian decay (max 5km): 0.5km → 0.89, 3km → 0.41 ✓ Correctly values closer highway much more

---

### Layer 1: Demographic Scoring

```python
def score_demographic(lat, lng, radius_km, threshold_pop):
    # Find census tracts within radius_km
    nearby = gdf_proj[distance_to_point <= radius_km * 1000]

    density_score = min(100, (avg_density / 10000) * 100)      # 10k/km² = perfect
    income_score  = min(100, ((avg_income - 30000) / 170000) * 100)  # $200k = perfect
    pop_score     = min(100, (total_pop / 100000) * 100)       # 100k = perfect

    composite = density_score * 0.4 + income_score * 0.35 + pop_score * 0.25

    # Hard threshold constraint
    if total_pop < threshold_population:
        composite *= 0.5   # 50% penalty if minimum population not met
```

**Sub-weights within demographic layer:**
- Population density: 40%
- Median income: 35%
- Total population: 25%

**Threshold constraint:** If `total_population_within_radius < threshold_population` (default 5,000), the score is halved. This implements the "hard requirement" specified in the problem statement.

---

### Layer 2: Transportation Scoring

```python
def score_transportation(lat, lng, radius_km):
    nearest_highway  = highways["distance_km"].min()
    nearest_arterial = arterials["distance_km"].min()
    road_count       = len(roads_within_radius)

    highway_score  = distance_decay(nearest_highway,  "gaussian", 5.0) * 100
    arterial_score = distance_decay(nearest_arterial, "linear",   3.0) * 100
    density_score  = min(100, road_count * 5)

    composite = highway_score * 0.5 + arterial_score * 0.3 + density_score * 0.2
```

**Sub-weights:**
- Highway proximity: 50% (most critical — drives large-area accessibility)
- Arterial road proximity: 30%
- Road density in radius: 20%

**Why Gaussian for highways:** A site 500m from a highway is dramatically better than one 3km away. The Gaussian bell curve models this non-linearity correctly.

---

### Layer 3: POI Scoring — The Competitor Density Model

This layer uses an **inverted U-curve** for competitor analysis:

```python
def score_poi(lat, lng, radius_km):
    # Anchor businesses (grocery, restaurant, cafe, gym, pharmacy)
    anchor_score = min(100, len(anchors) * 8)

    # Competitor density — inverted U-curve
    if   comp_count == 0:       market_score = 40   # No competitors = unproven market
    elif comp_count <= 5:       market_score = 80   # Some = market viability signal
    elif comp_count <= 15:      market_score = 60   # Getting saturated
    else:                       market_score = max(20, 60 - (comp_count - 15) * 3)

    # POI category diversity
    diversity_score = min(100, unique_categories * 15)

    composite = anchor_score * 0.4 + market_score * 0.4 + diversity_score * 0.2
```

**The insight:** Zero competitors is bad (no proven market). 1–5 competitors is ideal (market exists, not saturated). 15+ competitors means heavy saturation. This mirrors real retail site-selection logic.

---

### Layer 4: Land Use Scoring

```python
def score_land_use(lat, lng, radius_km):
    # Point-in-polygon — what zone is this exact coordinate in?
    containing = gdf[gdf.geometry.contains(point)]

    zone_scores = {
        "commercial":   100,   # Ideal
        "mixed":         80,   # Good
        "industrial":    60,   # Acceptable (warehouses)
        "institutional": 50,   # Neutral
        "residential":   40,   # Poor (permitting challenges)
        "park":          20,   # Very poor
    }

    # Also score nearby commercial area as a ratio
    commercial_ratio = commercial_area_nearby / 500_000  # normalize to 500k sqm
    commercial_score = commercial_ratio * 100

    composite = zone_score * 0.6 + commercial_score * 0.4
```

**Point-in-polygon** uses Shapely's `contains()` method. If the clicked coordinate falls inside a commercial zone polygon, it gets full score. Points not inside any polygon get 50 (neutral).

---

### Layer 5: Environmental Risk Scoring

```python
def score_environmental(lat, lng, radius_km):
    # Start at 100, subtract risk penalties
    risk_penalties = {
        "flood_zone":          40,   # Major risk
        "low_flood":           15,
        "earthquake_high":     35,   # Major risk
        "earthquake_medium":   15,
        "air_quality_poor":    25,
        "air_quality_moderate": 10,
        "air_quality_good":     0,
    }

    for risk_zone in zones_containing_point:
        penalty = risk_penalties[risk_type] * severity   # severity: 0.0–1.0
        total_penalty += penalty

    env_score = max(0, 100 - total_penalty)
```

**Note for renewable energy use case:** The environmental score is inverted in intent — sites in open, low-risk areas (high env score) are good for both traditional and renewable uses. For renewables, increasing the environmental weight to 45% naturally selects open undeveloped land.

---

### Composite Score Formula

```
composite_score = Σ (layer_score_i × normalized_weight_i)

normalized_weight_i = raw_weight_i / Σ(all raw_weights)
```

The normalization step ensures weights always sum to 1.0, even if the user sets sliders to non-summing values (e.g., all at 0.3 → each becomes 0.2).

### Grade Scale

| Score | Grade | Interpretation |
|---|---|---|
| 80–100 | A | Excellent — proceed with confidence |
| 70–79 | B | Good — minor concerns to address |
| 55–69 | C | Fair — significant trade-offs |
| 40–54 | D | Poor — major issues, proceed cautiously |
| 0–39 | F | Avoid — fundamental problems |

### H3 Index Assignment

Every scored site is tagged with its [Uber H3](https://h3geo.org/) hexagonal cell index at resolution 8 (~0.7km² per cell):

```python
# Supports both h3 v3 and v4 APIs
if hasattr(h3, 'latlng_to_cell'):
    h3_index = h3.latlng_to_cell(lat, lng, resolution=8)  # v4
else:
    h3_index = h3.geo_to_h3(lat, lng, 8)                  # v3
```

The H3 index enables spatial joins, aggregation, and consistent cell-based analysis across sessions.

---

## 7. Spatial Analysis — Hotspots & Clustering

### Overview

The hotspot system automatically scores every H3 hex cell covering the study area and classifies them into hot/warm/cold zones using DBSCAN clustering.

### Step 1: H3 Hexagonal Binning

```python
def generate_hotspot_analysis(bbox, use_case, weights, h3_resolution=8):
    min_lng, min_lat, max_lng, max_lat = bbox

    # Fill bbox with H3 cells (v4 API)
    poly = h3.LatLngPoly([
        (min_lat, min_lng), (max_lat, min_lng),
        (max_lat, max_lng), (min_lat, max_lng),
    ])
    h3_cells_set = h3.h3shape_to_cells(poly, h3_resolution)
    # Result: ~200 hexagons covering the SF bbox at resolution 8
```

**H3 Resolution 8 specs:**
- Average cell area: ~0.737 km²
- Average edge length: ~0.461 km
- ~200 cells cover the 20km² SF study area

### Step 2: Score Every Cell

```python
for cell in h3_cells_set:
    lat, lng = h3.cell_to_latlng(cell)   # get centroid
    result = compute_site_score(ScoreRequest(
        lat=lat, lng=lng,
        use_case=use_case,
        weights=weights,
        radius_km=0.5   # tighter radius for cell-level analysis
    ))
    cell_data.append({"h3_index": cell, "score": result.composite_score, ...})
```

Each cell is scored independently using the same scoring engine. ~200 calls, each ~20ms = ~4 seconds total (data is cached after first call).

### Step 3: DBSCAN Spatial Clustering

```python
# Build feature matrix: [lat, lng, score]
coords = np.array([[d["centroid_lat"], d["centroid_lng"]] for d in cell_data])
scores = np.array([d["score"] for d in cell_data])

# StandardScaler normalizes lat/lng/score to same scale
features = StandardScaler().fit_transform(
    np.column_stack([coords, scores.reshape(-1, 1)])
)

# DBSCAN: density-based clustering, no need to specify cluster count
db = DBSCAN(eps=0.3, min_samples=2).fit(features)
labels = db.labels_   # -1 = noise/isolated cell
```

**DBSCAN parameters:**
- `eps=0.3`: Maximum distance between two samples to be considered neighbors (in normalized space)
- `min_samples=2`: Minimum cluster size
- Label `-1`: Isolated cells not part of any cluster

### Step 4: Cluster Classification

```python
for cluster_id in unique_labels:
    avg_score = mean([cell["score"] for cell in cluster_cells])
    classification = "hot" if avg_score >= 70 else ("warm" if avg_score >= 50 else "cold")
```

### Frontend Hexagon Rendering

Since H3 JavaScript is not loaded in the browser, hexagons are approximated as regular polygons drawn around each cell centroid:

```javascript
const r = 0.003  // ~300m in degrees
const hexPoints = Array.from({length: 6}, (_, i) => {
    const angle = (i * 60 - 30) * Math.PI / 180
    return [lat + r * Math.cos(angle), lng + r * Math.sin(angle) * 1.3]
})
L.polygon(hexPoints, { fillColor: scoreToColor(cell.score), fillOpacity: opacity })
```

Opacity is score-weighted: `0.3 + (score/100) * 0.5` — high-scoring cells are more opaque, visually emphasizing hotspots.

---

## 8. Isochrone & Accessibility Analysis

### What Isochrones Show

An isochrone is a polygon showing all points reachable from a site within a given travel time. The app generates 3 concentric isochrones: 10, 20, and 30 minutes for drive/walk/transit modes.

### Algorithm

```python
SPEEDS = {"drive": 40, "walk": 5, "transit": 25}  # km/h

def compute_isochrone(lat, lng, minutes_list, mode):
    speed = SPEEDS[mode]
    point_proj = project_to_utm(lat, lng)   # EPSG:32610

    for minutes in minutes_list:
        radius_km = speed * minutes / 60    # theoretical max distance
        radius_m  = radius_km * 1000

        # Step 1: Base circle (60% of radius — represents non-road area)
        shapes = [point_proj.buffer(radius_m * 0.6)]

        # Step 2: Road corridor extensions
        for road in nearby_roads:
            road_dist = distance(point_proj, road.geometry)
            if road_dist < radius_m:
                multiplier = {"highway": 1.8, "arterial": 1.3, "local": 1.0}[road_type]
                extension = (radius_m - road_dist) * multiplier * 0.3
                shapes.append(road.geometry.buffer(extension))

        # Step 3: Union all shapes into one polygon
        isochrone_polygon = unary_union(shapes)

        # Step 4: Reproject back to WGS84 for GeoJSON output
        isochrone_wgs84 = reproject_to_wgs84(isochrone_polygon)
```

**Road extension logic:** Roads act as corridors extending reachability beyond a simple circle. A highway running away from the site allows cars to travel further in that direction. The `multiplier` values encode this (highways give 1.8× extension vs 1.0× for local roads).

### Population Catchment Estimation

```python
demo = data_loader.load_layer("demographic")
demo_centroids = demo.to_crs(32610).geometry.centroid.to_crs(4326)
within_mask = demo_centroids.within(isochrone_polygon_wgs84)
population_within = int(demo[within_mask]["population_total"].sum())
```

Census tract centroids that fall inside the isochrone polygon are summed for population estimates.

### Speed Reference Table

| Mode | Speed | 10 min radius | 20 min radius | 30 min radius |
|---|---|---|---|---|
| Drive | 40 km/h | 6.7 km | 13.3 km | 20 km |
| Transit | 25 km/h | 4.2 km | 8.3 km | 12.5 km |
| Walk | 5 km/h | 0.83 km | 1.67 km | 2.5 km |

---

## 9. REST API Reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs` (Swagger UI)

---

### POST /api/score/site

Score a single location.

**Request Body:**
```json
{
  "lat": 37.782,
  "lng": -122.418,
  "use_case": "retail",
  "weights": {
    "demographic": 0.35,
    "transportation": 0.20,
    "poi": 0.25,
    "land_use": 0.15,
    "environmental": 0.05
  },
  "radius_km": 1.0,
  "threshold_population": 5000
}
```

**Parameters:**
| Field | Type | Default | Description |
|---|---|---|---|
| `lat` | float | required | Latitude (-90 to 90) |
| `lng` | float | required | Longitude (-180 to 180) |
| `use_case` | string | "retail" | retail/warehouse/ev_charging/telecom/renewable |
| `weights` | object | null (equal) | Per-layer weights (auto-normalized) |
| `radius_km` | float | 1.0 | Analysis radius in kilometers |
| `threshold_population` | int | 5000 | Minimum population hard constraint |

**Response:**
```json
{
  "lat": 37.782,
  "lng": -122.418,
  "composite_score": 81.9,
  "grade": "A",
  "h3_index": "88283082a9fffff",
  "breakdowns": [
    {
      "layer_name": "demographic",
      "score": 85.6,
      "weight": 0.35,
      "contribution": 29.96,
      "factors": {
        "avg_population_density": 8234.1,
        "avg_median_income": 112000.0,
        "total_population_within_radius": 18420,
        "avg_median_age": 34.2,
        "threshold_population_met": true,
        "density_score": 82.3,
        "income_score": 48.2
      }
    },
    { "layer_name": "transportation", "score": 76.1, ... },
    { "layer_name": "poi", "score": 84.0, ... },
    { "layer_name": "land_use", "score": 64.0, ... },
    { "layer_name": "environmental", "score": 100.0, ... }
  ],
  "recommendations": [
    "Foot traffic and anchor tenant proximity are key retail success factors."
  ]
}
```

---

### POST /api/score/compare

Compare 2–10 sites and get a ranked recommendation.

**Request Body:** Array of ScoreRequest objects
```json
[
  {"lat": 37.782, "lng": -122.418, "use_case": "retail"},
  {"lat": 37.762, "lng": -122.435, "use_case": "retail"},
  {"lat": 37.799, "lng": -122.401, "use_case": "retail"}
]
```

**Response:**
```json
{
  "sites": [ ... array of SiteReadinessScore ... ],
  "ranking": [0, 2, 1],
  "recommendation": "Site 1 at (37.7820, -122.4180) is recommended with score 81.9/100 (Grade: A)."
}
```

`ranking` is an array of 0-based indices sorted from best to worst score.

---

### GET /api/layers/

List available layers.

**Response:** `{"layers": ["demographic", "roads", "poi", "land_use", "environmental", "competitor_locations"]}`

---

### GET /api/layers/{layer_name}

Fetch a full GeoJSON layer.

**Example:** `GET /api/layers/demographic`

**Response:** Full GeoJSON FeatureCollection (used by the frontend map to render each layer).

---

### GET /api/analysis/hotspots

Run H3 hexagonal binning + DBSCAN over a bounding box.

**Query Parameters:**
| Param | Default | Description |
|---|---|---|
| `min_lng` | -122.5 | Bounding box west edge |
| `min_lat` | 37.7 | Bounding box south edge |
| `max_lng` | -122.35 | Bounding box east edge |
| `max_lat` | 37.82 | Bounding box north edge |
| `use_case` | "retail" | Use case for scoring |
| `h3_resolution` | 8 | H3 resolution (7=larger cells, 9=smaller) |

**Response:**
```json
{
  "h3_cells": [
    {
      "h3_index": "88283082a9fffff",
      "score": 81.9,
      "centroid_lat": 37.782,
      "centroid_lng": -122.418,
      "cluster_id": 2
    },
    ...
  ],
  "clusters": [
    {
      "cluster_id": 2,
      "centroid": [37.78, -122.41],
      "size": 12,
      "avg_score": 78.4,
      "classification": "hot"
    },
    ...
  ]
}
```

---

### GET /api/isochrone/

Compute travel-time isochrones from a point.

**Query Parameters:**
| Param | Default | Description |
|---|---|---|
| `lat` | required | Site latitude |
| `lng` | required | Site longitude |
| `mode` | "drive" | drive / walk / transit |
| `minutes` | "10,20,30" | Comma-separated time intervals |

**Response:**
```json
{
  "lat": 37.782,
  "lng": -122.418,
  "isochrones": [
    {
      "minutes": 10,
      "mode": "drive",
      "geojson_geometry": { "type": "Polygon", "coordinates": [...] },
      "population_within": 45230,
      "area_sqkm": 12.4
    },
    { "minutes": 20, "population_within": 124800, "area_sqkm": 38.7, ... },
    { "minutes": 30, "population_within": 298400, "area_sqkm": 94.2, ... }
  ]
}
```

---

### POST /api/export/json

Download a full site analysis report as JSON.

**Request Body:** Single ScoreRequest

**Response:** `application/json` file download (`site_report_YYYYMMDD_HHMMSS.json`)

---

### POST /api/export/csv

Export multiple site scores as CSV.

**Request Body:** Array of ScoreRequest objects

**Response:** `text/csv` file download (`site_comparison.csv`)

CSV columns: `lat, lng, composite_score, grade, demographic, transportation, poi, land_use, environmental`

---

## 10. Frontend — UI Walkthrough

### Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  Left Sidebar (320px) │       Map Canvas        │  Score Panel (384px)│
│                       │                         │  (slides in on click)│
│  ┌─────────────────┐  │  [CartoDB Dark tiles]   │                     │
│  │ GeoSite Analyzer│  │                         │  ┌───────────────┐  │
│  │ AI Location Intl│  │  [Layer overlays]       │  │ Score Circle  │  │
│  └─────────────────┘  │                         │  │   81 / 100    │  │
│                       │  [Hex hotspots]         │  │   Grade: A    │  │
│  Use Case             │                         │  └───────────────┘  │
│  ● Retail Store  🏪   │  [Isochrone rings]      │                     │
│  ○ Warehouse     🏭   │                         │  [Radar Chart]      │
│  ○ EV Charging   ⚡   │  [Score markers]        │                     │
│  ○ Telecom Tower 📡   │                         │  [Layer Bars]       │
│  ○ Renewable     ☀️   │  [Pinned site markers]  │                     │
│                       │                         │  [Recommendations]  │
│  Layer Weights        │                         │                     │
│  Demographic  [===]35%│                         │  [Pin] [Export]     │
│  Transport    [==] 20%│                         │                     │
│  POI          [===]25%│                         └─────────────────────┘
│  Land Use     [=]  15%│
│  Environmental [<]  5%│
│                       │
│  Data Layers          │
│  ▣ Demographics       │
│  ▣ Road Network       │
│  ▣ Points of Interest │
│  □ Land Use / Zoning  │
│  □ Environmental Risk │
│  □ Competitors        │
│                       │
│  Analysis Tools       │
│  [Show Hotspots]      │
│  Drive ▾ [Isochrone]  │
└───────────────────────┘
Bottom Bar (when sites pinned):
┌──────────────────────────────────────────────────────────────────────┐
│ Pinned Sites (3)  #1 81.9/100 (A)  #2 66.1/100 (C)  #3 74.3/100 (B)│
│                                              [Compare] [Export CSV]   │
└──────────────────────────────────────────────────────────────────────┘
```

---

### Action: Click Map to Score a Site

1. Click anywhere on the map
2. React calls `api.scoresite(lat, lng, useCase, weights)`
3. "Analyzing site..." spinner appears at top center
4. API responds in ~100–200ms
5. Score marker appears at clicked point (colored circle showing score number)
6. Popup opens showing score/grade
7. Score Panel slides in from right with full breakdown
8. If isochrone is enabled, a second API call fetches catchment rings simultaneously

---

### Action: Switch Use Case

Click any use case button in the left sidebar:

| Use Case | Effect |
|---|---|
| Retail Store | Weights → Demo 35%, POI 25%, Transport 20%, Land 15%, Env 5% |
| Warehouse | Weights → Transport 45%, Land 35%, Env 10%, Demo 5%, POI 5% |
| EV Charging | Weights → Transport 45%, Land 20%, Demo 15%, Env 10%, POI 10% |
| Telecom Tower | Weights → Land 30%, Demo 25%, Env 25%, Transport 15%, POI 5% |
| Renewable Energy | Weights → Env 45%, Land 35%, Transport 10%, Demo 5%, POI 5% |

The weight sliders instantly update to reflect the new preset. You can then fine-tune by dragging individual sliders.

---

### Action: Toggle Data Layers

Click any layer in the "Data Layers" section. Active layers show a colored dot.

| Layer | Visual Style |
|---|---|
| Demographics | Green/red choropleth fill on census tract polygons |
| Road Network | Colored polylines by road type |
| Points of Interest | Colored circles by category |
| Land Use / Zoning | Color-coded zone polygons |
| Environmental Risk | Risk-colored overlapping polygons |
| Competitors | Red circles |

Hover over any feature to see a tooltip with its properties.

---

### Action: Show Hotspots

Click "Show Hotspots" in Analysis Tools:
1. Triggers `GET /api/analysis/hotspots` with current use case
2. Loading state: button shows "Analyzing..."
3. ~3–5 seconds for ~200 hexagon scores
4. Map fills with colored hexagons (green=high, red=low)
5. Hex opacity is score-weighted (higher score = more opaque = more prominent)
6. Hover any hex to see its score and cluster ID
7. Click "Hide Hotspots" to clear

Changing use case clears hotspot data (requires re-analysis for new use case weights).

---

### Action: Isochrone Analysis

1. Select transport mode: Drive / Walk / Transit
2. Click "Isochrone" button (it stays active)
3. Click any map location → site is scored AND isochrones are fetched
4. Three concentric rings appear:
   - Inner ring (purple): 10-minute catchment
   - Middle ring (blue): 20-minute catchment
   - Outer ring (cyan): 30-minute catchment
5. Hover each ring to see population count and area
6. Score Panel shows a "Catchment Areas" table with population/km² per ring
7. Click "Hide Iso" to disable

---

### Action: Pin & Compare Sites

1. Score a site → click "Pin Site" in Score Panel
2. Site appears in the bottom comparison bar with index #1
3. Pin up to 10 sites across different locations
4. Click "Compare" to get server-side ranking
5. Recommendation text appears showing the best site
6. Click "Export CSV" to download all pinned sites as a spreadsheet

Pinned sites show as smaller numbered markers on the map.

---

### Action: Export

**Single site JSON:** Click "Export" in the Score Panel → downloads `site_report_YYYYMMDD_HHMMSS.json` with full breakdown including all factor values.

**Multi-site CSV:** Click "Export CSV" in comparison bar → downloads `site_comparison.csv` with lat, lng, composite score, grade, and all 5 layer scores as columns.

---

## 11. Component Reference

### App.jsx

Root component. Owns all application state:

| State | Type | Description |
|---|---|---|
| `selectedUseCase` | string | Active use case ID |
| `weights` | object | Current layer weight values |
| `activeLayers` | string[] | Layers currently shown on map |
| `selectedSite` | object | Currently displayed site score |
| `pinnedSites` | object[] | Sites in comparison bar |
| `isScoring` | bool | Loading state for site scoring |
| `showHotspots` | bool | Hotspot overlay visible |
| `hotspotData` | object | H3 + DBSCAN results |
| `isochroneData` | object | Isochrone polygons |
| `showIsochrone` | bool | Isochrone overlay active |
| `isochroneMode` | string | drive/walk/transit |

---

### Map.jsx

Manages the Leaflet map instance and all overlay layers. Uses `useRef` to persist the map instance across re-renders. Key refs:

| Ref | Description |
|---|---|
| `mapInstanceRef` | The Leaflet Map object |
| `layerGroupsRef` | Dict of active LayerGroup objects |
| `selectedMarkerRef` | Current site marker |
| `pinnedMarkersRef` | Array of pinned site markers |
| `hotspotLayerRef` | LayerGroup of hex polygons |
| `isochroneLayerRef` | LayerGroup of isochrone polygons |

Layer rendering uses `useEffect` hooks that watch `activeLayers`, `selectedSite`, `pinnedSites`, `hotspotData`, and `isochroneData` for changes.

---

### ScorePanel.jsx

Right panel showing full site analysis. Features:
- Score circle (colored by score, border matches score color)
- Grade badge
- Recharts RadarChart showing all 5 layer scores
- Expandable breakdown bars (click any bar to see raw factor values)
- Isochrone catchment table (if active)
- Recommendations list
- Pin and Export buttons

---

### LayerPanel.jsx

Left sidebar section for toggling data layers. Each layer button toggles its ID in the `activeLayers` array in App state. Map.jsx watches this array and loads/removes Leaflet LayerGroups accordingly.

---

### SiteComparison.jsx

Bottom bar component. Renders each pinned site as a chip showing its rank, score, grade, and coordinates. Calls `POST /api/score/compare` with all pinned sites when Compare is clicked. Downloads CSV via `POST /api/export/csv`.

---

### utils/api.js

Axios wrapper for all API calls. All calls use the `/api` prefix which Vite proxies to `http://localhost:8000` in development.

```javascript
export const api = {
  scoresite: (lat, lng, useCase, weights, radiusKm = 1.0) =>
    axios.post('/api/score/site', { lat, lng, use_case: useCase, weights, radius_km: radiusKm }),

  compareSites: (sites) =>
    axios.post('/api/score/compare', sites),

  getLayer: (layerName) =>
    axios.get(`/api/layers/${layerName}`),

  getHotspots: (bbox, useCase, h3Resolution = 8) =>
    axios.get('/api/analysis/hotspots', { params: { min_lng, min_lat, max_lng, max_lat, use_case, h3_resolution } }),

  getIsochrone: (lat, lng, mode = 'drive', minutes = '10,20,30') =>
    axios.get('/api/isochrone', { params: { lat, lng, mode, minutes } }),

  exportJson: (scoreRequest) =>
    axios.post('/api/export/json', scoreRequest, { responseType: 'blob' }),

  exportCsv: (scoreRequests) =>
    axios.post('/api/export/csv', scoreRequests, { responseType: 'blob' }),
}
```

---

## 12. Use Case Presets

### Weight Rationale

**Retail Store**
```
demographic: 0.35   High — foot traffic and spending power are everything
transportation: 0.20  Medium — accessibility matters but not #1
poi: 0.25          High — anchor tenants and market viability
land_use: 0.15     Medium — commercial zoning important
environmental: 0.05  Low — rarely a dealbreaker for retail
```

**Warehouse / Distribution Center**
```
demographic: 0.05   Low — workers commute, customers don't visit
transportation: 0.45 Critical — truck routes, highway access
poi: 0.05          Minimal — doesn't benefit from nearby cafes
land_use: 0.35     High — industrial zoning required
environmental: 0.10  Moderate — flood risk matters for inventory
```

**EV Charging Station**
```
demographic: 0.15   Moderate — needs EV-owning population nearby
transportation: 0.45 Critical — highway exits and high-traffic roads
poi: 0.10          Low — nearby businesses keep customers occupied
land_use: 0.20     Moderate — needs parking/commercial area
environmental: 0.10  Low
```

**Telecom Tower**
```
demographic: 0.25   Important — need to serve population centers
transportation: 0.15  Low — tower just needs access road
poi: 0.05          Minimal
land_use: 0.30     High — industrial/institutional zoning often needed
environmental: 0.25  High — wind/earthquake risk affects tower stability
```

**Renewable Energy Installation**
```
demographic: 0.05   Minimal — remote sites fine
transportation: 0.10  Low — just needs grid connection access
poi: 0.05          None
land_use: 0.35     High — needs open undeveloped land
environmental: 0.45 Critical — terrain, flood risk, air currents
```

---

## 13. Export System

### JSON Export

Full structured report for one site:

```json
{
  "lat": 37.782,
  "lng": -122.418,
  "composite_score": 81.9,
  "grade": "A",
  "h3_index": "88283082a9fffff",
  "breakdowns": [
    {
      "layer_name": "demographic",
      "score": 85.6,
      "weight": 0.35,
      "contribution": 29.96,
      "factors": {
        "avg_population_density": 8234.1,
        "avg_median_income": 112000.0,
        "total_population_within_radius": 18420,
        "avg_median_age": 34.2,
        "threshold_population_met": true,
        "density_score": 82.3,
        "income_score": 48.2
      }
    }
  ],
  "recommendations": ["Foot traffic and anchor tenant proximity are key retail success factors."]
}
```

### CSV Export

Multi-site comparison spreadsheet:

```
lat,lng,composite_score,grade,demographic,transportation,poi,land_use,environmental
37.782,-122.418,81.9,A,85.6,76.1,84.0,64.0,100.0
37.762,-122.435,66.1,C,72.3,58.4,61.2,52.0,88.0
37.799,-122.401,74.3,B,69.1,80.2,72.5,71.0,79.0
```

---

## 14. Evaluation Criteria Mapping

| Criterion | Implementation | Evidence |
|---|---|---|
| **Geospatial layers integrated** | 6 layers: demographic, roads, POI, land use, environmental, competitors | `backend/data/*.geojson`, all rendered on map |
| **Scoring model configurability** | 5 configurable weights, 3 distance-decay functions, inverted-U competitor curve, population threshold constraint | `scoring.py` |
| **Scoring model accuracy** | Graded A-F, per-layer factor transparency, expert-tunable weights | ScorePanel breakdown + factor drilldown |
| **Spatial analysis quality** | H3 resolution-8 hexagonal binning + DBSCAN clustering + hot/warm/cold classification | `clustering.py` |
| **Map interface usability** | Dark-mode Leaflet map, 6 toggleable layers, score markers, hotspot hexes, isochrone rings, draw polygon, site pinning | `Map.jsx` |
| **Accessibility analysis** | Drive/walk/transit isochrones at 10/20/30 min with road-network adjustment and population catchment | `isochrone_service.py` |
| **Supported formats** | GeoJSON (primary), WKT (via Shapely internally), Shapefile via Fiona | All data files |
| **Distance-decay functions** | Gaussian, linear, inverse — applied per layer based on characteristic | `distance_decay()` in `scoring.py` |
| **Competitive density analysis** | Inverted U-curve: 0 competitors=40, 1-5=80, 6-15=60, 15+=decreasing | `score_poi()` |
| **Threshold constraints** | `threshold_population` hard constraint with 50% score penalty if unmet | `score_demographic()` |
| **H3 hexagonal binning** | Resolution-8 cells, ~200 cells per SF bbox | `clustering.py` |
| **DBSCAN clustering** | Noise-robust density clustering on normalized lat/lng/score features | `clustering.py` |
| **Export** | JSON (single site) and CSV (multi-site comparison) | `export.py` |
| **Site comparison** | Up to 10 sites, server-side ranked with recommendation | `POST /api/score/compare` |

---

*Built for the GeoSpatial Site Readiness Analyzer Hackathon Challenge.*
*Tech: FastAPI · GeoPandas · H3 · scikit-learn · React · Leaflet · Recharts · Tailwind*
