"""Site readiness scoring engine with configurable weights and distance-decay."""
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from app.models.schemas import ScoreRequest, SiteReadinessScore, ScoreBreakdown, LayerWeights
from app.services.data_loader import data_loader


def distance_decay(distance_km: float, decay_type: str = "inverse", max_dist_km: float = 5.0) -> float:
    """Apply distance decay function. Returns 0-1 multiplier."""
    if distance_km >= max_dist_km:
        return 0.0
    ratio = distance_km / max_dist_km
    if decay_type == "inverse":
        return 1.0 / (1.0 + distance_km * 2)
    elif decay_type == "gaussian":
        return float(np.exp(-0.5 * (ratio * 3) ** 2))
    elif decay_type == "linear":
        return 1.0 - ratio
    return 1.0 - ratio


def score_demographic(lat: float, lng: float, radius_km: float, threshold_pop: int) -> tuple:
    """Score demographic suitability (0-100)."""
    gdf = data_loader.load_layer("demographic")
    point = Point(lng, lat)

    gdf_proj = gdf.to_crs(epsg=32610)
    point_proj = gpd.GeoSeries([point], crs=4326).to_crs(epsg=32610).iloc[0]

    gdf_proj_copy = gdf_proj.copy()
    gdf_proj_copy["_dist"] = gdf_proj_copy.geometry.distance(point_proj)
    nearby = gdf_proj_copy[gdf_proj_copy["_dist"] <= radius_km * 1000]

    if nearby.empty:
        nearby = gdf_proj_copy

    avg_density = float(nearby["population_density"].mean())
    avg_income = float(nearby["median_income"].mean())
    total_pop = int(nearby["population_total"].sum())
    avg_age = float(nearby["median_age"].mean())

    # Normalize scores
    density_score = min(100.0, (avg_density / 10000) * 100)
    income_score = min(100.0, ((avg_income - 30000) / 170000) * 100)
    pop_score = min(100.0, (total_pop / 100000) * 100)

    # Threshold constraint
    threshold_met = total_pop >= threshold_pop

    composite = density_score * 0.4 + income_score * 0.35 + pop_score * 0.25
    if not threshold_met:
        composite *= 0.5  # Hard penalty

    factors = {
        "avg_population_density": round(avg_density, 1),
        "avg_median_income": round(avg_income, 0),
        "total_population_within_radius": total_pop,
        "avg_median_age": round(avg_age, 1),
        "threshold_population_met": threshold_met,
        "density_score": round(density_score, 1),
        "income_score": round(income_score, 1),
    }
    return min(100.0, max(0.0, composite)), factors


def score_transportation(lat: float, lng: float, radius_km: float) -> tuple:
    """Score transportation accessibility (0-100)."""
    gdf = data_loader.load_layer("roads")
    point = Point(lng, lat)

    gdf_proj = gdf.to_crs(epsg=32610)
    point_proj = gpd.GeoSeries([point], crs=4326).to_crs(epsg=32610).iloc[0]

    gdf_proj_copy = gdf_proj.copy()
    gdf_proj_copy["distance_km"] = gdf_proj_copy.geometry.distance(point_proj) / 1000
    nearby = gdf_proj_copy[gdf_proj_copy["distance_km"] <= radius_km * 2]

    if nearby.empty:
        return 30.0, {
            "highway_access": False,
            "road_density": 0,
            "nearest_highway_km": 99.0,
        }

    # Highway proximity (most important)
    highways = nearby[nearby["road_type"] == "highway"]
    nearest_highway = float(highways["distance_km"].min()) if not highways.empty else 99.0
    highway_score = distance_decay(nearest_highway, "gaussian", 5.0) * 100

    # Arterial roads
    arterials = nearby[nearby["road_type"] == "arterial"]
    nearest_arterial = float(arterials["distance_km"].min()) if not arterials.empty else 99.0
    arterial_score = distance_decay(nearest_arterial, "linear", 3.0) * 100

    # Road density
    road_count = int(len(nearby[nearby["distance_km"] <= radius_km]))
    density_score = min(100.0, road_count * 5.0)

    composite = highway_score * 0.5 + arterial_score * 0.3 + density_score * 0.2

    factors = {
        "nearest_highway_km": round(nearest_highway, 2),
        "nearest_arterial_km": round(nearest_arterial, 2),
        "road_count_in_radius": road_count,
        "highway_score": round(highway_score, 1),
        "arterial_score": round(arterial_score, 1),
        "density_score": round(density_score, 1),
    }
    return min(100.0, max(0.0, composite)), factors


def score_poi(lat: float, lng: float, radius_km: float) -> tuple:
    """Score POI landscape — complementary businesses positive, competitors assessed. (0-100)."""
    gdf = data_loader.load_layer("poi")
    comp = data_loader.load_layer("competitor_locations")
    point = Point(lng, lat)

    gdf_proj = gdf.to_crs(epsg=32610)
    comp_proj = comp.to_crs(epsg=32610)
    point_proj = gpd.GeoSeries([point], crs=4326).to_crs(epsg=32610).iloc[0]

    gdf_proj_copy = gdf_proj.copy()
    comp_proj_copy = comp_proj.copy()
    gdf_proj_copy["dist"] = gdf_proj_copy.geometry.distance(point_proj) / 1000
    comp_proj_copy["dist"] = comp_proj_copy.geometry.distance(point_proj) / 1000

    nearby_poi = gdf_proj_copy[gdf_proj_copy["dist"] <= radius_km]
    nearby_comp = comp_proj_copy[comp_proj_copy["dist"] <= radius_km]

    # Complementary businesses (anchor effect)
    anchor_categories = ["grocery", "restaurant", "cafe", "gym", "pharmacy"]
    anchors = nearby_poi[nearby_poi["category"].isin(anchor_categories)]
    anchor_score = min(100.0, len(anchors) * 8.0)

    # Competitor density analysis (inverted U-curve)
    comp_count = len(nearby_comp)
    if comp_count == 0:
        market_score = 40.0  # No proof of market
    elif comp_count <= 5:
        market_score = 80.0  # Some competition = market viability
    elif comp_count <= 15:
        market_score = 60.0  # Getting crowded
    else:
        market_score = max(20.0, 60.0 - (comp_count - 15) * 3.0)  # Too many

    # POI diversity
    categories = int(nearby_poi["category"].nunique())
    diversity_score = min(100.0, categories * 15.0)

    composite = anchor_score * 0.4 + market_score * 0.4 + diversity_score * 0.2

    factors = {
        "anchor_businesses_count": len(anchors),
        "competitor_count": comp_count,
        "poi_diversity_categories": categories,
        "total_poi_in_radius": len(nearby_poi),
        "anchor_score": round(anchor_score, 1),
        "market_viability_score": round(market_score, 1),
        "diversity_score": round(diversity_score, 1),
    }
    return min(100.0, max(0.0, composite)), factors


def score_land_use(lat: float, lng: float, radius_km: float) -> tuple:
    """Score land use and zoning suitability (0-100)."""
    gdf = data_loader.load_layer("land_use")
    point = Point(lng, lat)

    gdf_proj = gdf.to_crs(epsg=32610)
    point_proj = gpd.GeoSeries([point], crs=4326).to_crs(epsg=32610).iloc[0]

    containing = gdf[gdf.geometry.contains(point)]

    zone_scores = {
        "commercial": 100,
        "mixed": 80,
        "industrial": 60,
        "residential": 40,
        "institutional": 50,
        "park": 20,
    }

    if not containing.empty:
        zone_type = containing.iloc[0]["zone_type"]
        zone_score = float(zone_scores.get(zone_type, 50))
        point_zone = zone_type
    else:
        zone_score = 50.0
        point_zone = "unknown"

    gdf_proj_copy = gdf_proj.copy()
    gdf_proj_copy["dist"] = gdf_proj_copy.geometry.distance(point_proj) / 1000
    nearby = gdf_proj_copy[gdf_proj_copy["dist"] <= radius_km]

    commercial_area = float(
        nearby[nearby["zone_type"].isin(["commercial", "mixed"])]["area_sqm"].sum()
    )
    commercial_ratio = min(1.0, commercial_area / 500000.0)
    commercial_score = commercial_ratio * 100.0

    composite = zone_score * 0.6 + commercial_score * 0.4

    factors = {
        "point_zone_type": point_zone,
        "zone_suitability_score": zone_score,
        "commercial_area_sqm_nearby": round(commercial_area, 0),
        "commercial_ratio_nearby": round(commercial_ratio, 3),
    }
    return min(100.0, max(0.0, composite)), factors


def score_environmental(lat: float, lng: float, radius_km: float) -> tuple:
    """Score environmental risk (higher = less risk = better) (0-100)."""
    gdf = data_loader.load_layer("environmental")
    point = Point(lng, lat)

    gdf_proj = gdf.to_crs(epsg=32610)
    point_proj = gpd.GeoSeries([point], crs=4326).to_crs(epsg=32610).iloc[0]

    containing = gdf[gdf.geometry.contains(point)]

    risk_penalties = {
        "flood_zone": 40,
        "low_flood": 15,
        "earthquake_high": 35,
        "earthquake_medium": 15,
        "air_quality_poor": 25,
        "air_quality_moderate": 10,
        "air_quality_good": 0,
    }

    total_penalty = 0.0
    risks_present = []
    if not containing.empty:
        for _, row in containing.iterrows():
            penalty = risk_penalties.get(row["risk_type"], 0) * row["severity"]
            total_penalty += penalty
            risks_present.append(row["risk_type"])

    env_score = max(0.0, 100.0 - total_penalty)

    gdf_proj_copy = gdf_proj.copy()
    gdf_proj_copy["dist"] = gdf_proj_copy.geometry.distance(point_proj) / 1000
    nearby_risks = gdf_proj_copy[
        (gdf_proj_copy["dist"] <= radius_km)
        & (gdf_proj_copy["risk_type"].str.contains("flood|earthquake|poor", regex=True))
    ]

    factors = {
        "risks_at_point": risks_present,
        "total_risk_penalty": round(total_penalty, 1),
        "nearby_high_risk_zones": int(len(nearby_risks)),
        "in_flood_zone": "flood_zone" in risks_present,
        "in_earthquake_zone": any("earthquake" in r for r in risks_present),
    }
    return min(100.0, max(0.0, env_score)), factors


def get_recommendations(breakdowns: list, use_case: str) -> list:
    """Generate actionable recommendations based on scores."""
    recs = []
    score_map = {b.layer_name: b.score for b in breakdowns}

    if score_map.get("demographic", 100) < 50:
        recs.append(
            "Low demographic score: Consider higher-density areas or increase marketing "
            "budget to compensate."
        )
    if score_map.get("transportation", 100) < 50:
        recs.append(
            "Poor transportation access: Factor in last-mile delivery costs and customer "
            "accessibility challenges."
        )
    if score_map.get("poi", 100) < 40:
        recs.append(
            "Limited POI ecosystem: May face slow initial traffic. "
            "Consider anchor tenant partnerships."
        )
    if score_map.get("land_use", 100) < 60:
        recs.append(
            "Zoning concerns: Verify commercial permits are obtainable before committing to this site."
        )
    if score_map.get("environmental", 100) < 60:
        recs.append(
            "Environmental risks detected: Obtain environmental impact assessment and "
            "flood/earthquake insurance."
        )

    use_case_tips = {
        "ev_charging": (
            "Prioritize highway proximity and parking availability for EV charging stations."
        ),
        "warehouse": (
            "Industrial zoning and highway access are critical — prioritize logistics efficiency."
        ),
        "retail": (
            "Foot traffic and anchor tenant proximity are key retail success factors."
        ),
        "telecom": (
            "Elevation and clear line-of-sight to population centers is essential for towers."
        ),
        "renewable": (
            "Environmental layer is inverted for renewables — open land and "
            "sun/wind exposure matter."
        ),
    }
    if use_case in use_case_tips:
        recs.append(use_case_tips[use_case])

    if not recs:
        recs.append(
            "This site shows strong fundamentals across all evaluated dimensions."
        )

    return recs


def compute_grade(score: float) -> str:
    if score >= 80:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 55:
        return "C"
    elif score >= 40:
        return "D"
    return "F"


def compute_site_score(req: ScoreRequest) -> SiteReadinessScore:
    """Main scoring function."""
    import h3

    weights = req.weights or LayerWeights()
    w = weights.dict()

    # Normalize weights
    total_w = sum(w.values())
    if total_w == 0:
        total_w = 1.0

    # Score each layer
    layers = [
        ("demographic", score_demographic(req.lat, req.lng, req.radius_km, req.threshold_population)),
        ("transportation", score_transportation(req.lat, req.lng, req.radius_km)),
        ("poi", score_poi(req.lat, req.lng, req.radius_km)),
        ("land_use", score_land_use(req.lat, req.lng, req.radius_km)),
        ("environmental", score_environmental(req.lat, req.lng, req.radius_km)),
    ]

    breakdowns = []
    composite = 0.0

    for layer_name, (score, factors) in layers:
        weight = w.get(layer_name, 0.2)
        contribution = score * (weight / total_w)
        composite += contribution
        breakdowns.append(
            ScoreBreakdown(
                layer_name=layer_name,
                score=round(score, 1),
                weight=round(weight / total_w, 3),
                contribution=round(contribution, 2),
                factors=factors,
            )
        )

    # h3 v4: latlng_to_cell; h3 v3: geo_to_h3
    if hasattr(h3, 'latlng_to_cell'):
        h3_index = h3.latlng_to_cell(req.lat, req.lng, 8)
    else:
        h3_index = h3.geo_to_h3(req.lat, req.lng, 8)

    return SiteReadinessScore(
        lat=req.lat,
        lng=req.lng,
        composite_score=round(composite, 1),
        grade=compute_grade(composite),
        breakdowns=breakdowns,
        h3_index=h3_index,
        recommendations=get_recommendations(breakdowns, req.use_case),
    )
