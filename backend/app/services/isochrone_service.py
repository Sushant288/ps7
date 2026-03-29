"""Drive-time and walk-time isochrone computation using geometric approximation."""
import geopandas as gpd
from shapely.geometry import Point, mapping
from shapely.ops import unary_union
from app.services.data_loader import data_loader
from typing import List, Dict, Any

# Average speeds in km/h
SPEEDS = {"drive": 40, "walk": 5, "transit": 25}


def compute_isochrone(
    lat: float,
    lng: float,
    minutes_list: List[int] = None,
    mode: str = "drive",
) -> List[Dict[str, Any]]:
    """Compute approximate isochrone as road-network-adjusted polygon."""
    if minutes_list is None:
        minutes_list = [10, 20, 30]

    speed = SPEEDS.get(mode, 40)
    point = Point(lng, lat)

    gdf_roads = data_loader.load_layer("roads")
    point_proj = gpd.GeoSeries([point], crs=4326).to_crs(epsg=32610).iloc[0]

    isochrones = []

    for minutes in minutes_list:
        radius_km = speed * minutes / 60.0
        radius_m = radius_km * 1000.0

        roads_proj = gdf_roads.to_crs(epsg=32610).copy()
        roads_proj["dist"] = roads_proj.geometry.distance(point_proj)
        nearby_roads = roads_proj[roads_proj["dist"] <= radius_m * 1.5]

        # Build buffered road corridors + base circle
        shapes = [point_proj.buffer(radius_m * 0.6)]  # base reachable area

        for _, road in nearby_roads.iterrows():
            road_dist = float(road["dist"])
            if road_dist < radius_m:
                road_type_multiplier = {
                    "highway": 1.8,
                    "arterial": 1.3,
                    "local": 1.0,
                }.get(road.get("road_type", "local"), 1.0)
                extension = (radius_m - road_dist) * road_type_multiplier * 0.3
                shapes.append(road["geometry"].buffer(extension))

        union_shape = unary_union(shapes)

        # Convert back to WGS84
        isochrone_gdf = gpd.GeoSeries([union_shape], crs=32610).to_crs(4326)
        isochrone_geom = isochrone_gdf.iloc[0]

        # Estimate population within isochrone
        demo = data_loader.load_layer("demographic")
        try:
            # Project to UTM first for accurate centroid calculation
            demo_proj = demo.to_crs(epsg=32610)
            demo_centroids_proj = demo_proj.geometry.centroid
            # Convert centroids back to WGS84 for within() check
            demo_centroids_wgs = demo_centroids_proj.to_crs(epsg=4326)
            within_mask = demo_centroids_wgs.within(isochrone_geom)
            within_pop = int(demo[within_mask]["population_total"].sum())
        except Exception:
            within_pop = 0

        area_sqkm = float(union_shape.area) / 1e6  # m² to km²

        isochrones.append({
            "minutes": minutes,
            "mode": mode,
            "geojson_geometry": mapping(isochrone_geom),
            "population_within": within_pop,
            "area_sqkm": round(area_sqkm, 2),
        })

    return isochrones
