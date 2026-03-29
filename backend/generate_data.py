#!/usr/bin/env python3
"""
Generate realistic synthetic GeoJSON datasets for San Francisco Bay Area.
Bounding box: (-122.5, 37.7, -122.35, 37.82)
"""

import json
import random
import math
import os
from pathlib import Path

random.seed(42)

# SF Bay Area bounding box
MIN_LNG, MIN_LAT, MAX_LNG, MAX_LAT = -122.5, 37.7, -122.35, 37.82

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def rand_lng():
    return random.uniform(MIN_LNG, MAX_LNG)


def rand_lat():
    return random.uniform(MIN_LAT, MAX_LAT)


def rand_point():
    return [rand_lng(), rand_lat()]


def biased_point(center_lng, center_lat, spread_lng=0.02, spread_lat=0.015):
    """Generate a point biased towards a center location."""
    lng = center_lng + random.gauss(0, spread_lng)
    lat = center_lat + random.gauss(0, spread_lat)
    lng = max(MIN_LNG, min(MAX_LNG, lng))
    lat = max(MIN_LAT, min(MAX_LAT, lat))
    return [lng, lat]


def make_bbox_polygon(min_lng, min_lat, max_lng, max_lat):
    return [
        [min_lng, min_lat],
        [max_lng, min_lat],
        [max_lng, max_lat],
        [min_lng, max_lat],
        [min_lng, min_lat],
    ]


def make_polygon_around(center_lng, center_lat, width_deg, height_deg):
    half_w = width_deg / 2
    half_h = height_deg / 2
    return [[
        [center_lng - half_w, center_lat - half_h],
        [center_lng + half_w, center_lat - half_h],
        [center_lng + half_w, center_lat + half_h],
        [center_lng - half_w, center_lat + half_h],
        [center_lng - half_w, center_lat - half_h],
    ]]


def make_irregular_polygon(center_lng, center_lat, base_radius_deg, n_vertices=6):
    """Create an irregular polygon around a center point."""
    vertices = []
    for i in range(n_vertices):
        angle = (2 * math.pi * i / n_vertices) + random.uniform(-0.2, 0.2)
        r = base_radius_deg * random.uniform(0.7, 1.3)
        # Adjust for lat/lng aspect ratio
        lng_r = r * 1.3
        lat_r = r
        vertices.append([
            center_lng + lng_r * math.cos(angle),
            center_lat + lat_r * math.sin(angle),
        ])
    # Close the ring by repeating the exact first vertex
    ring = vertices + [vertices[0]]
    return [ring]


# ─────────────────────────────────────────────
# 1. DEMOGRAPHIC (50 census tract polygons)
# ─────────────────────────────────────────────

# SF neighborhoods approximate grid layout
SF_DISTRICTS = [
    # (name, center_lng, center_lat, pop_density_factor, income_factor)
    ("Downtown/FiDi", -122.398, 37.795, 1.0, 1.0),
    ("SoMa", -122.404, 37.779, 0.85, 0.8),
    ("Mission", -122.419, 37.763, 0.75, 0.55),
    ("Castro", -122.435, 37.762, 0.70, 0.75),
    ("Haight", -122.446, 37.769, 0.65, 0.60),
    ("Richmond", -122.472, 37.778, 0.55, 0.65),
    ("Sunset", -122.485, 37.754, 0.50, 0.60),
    ("Nob Hill", -122.414, 37.793, 0.80, 0.85),
    ("Marina", -122.437, 37.803, 0.65, 0.90),
    ("North Beach", -122.408, 37.800, 0.78, 0.80),
]

def generate_demographic():
    features = []
    tract_id = 1001

    # Create a grid of census tracts
    lng_steps = 10
    lat_steps = 5
    lng_width = (MAX_LNG - MIN_LNG) / lng_steps
    lat_height = (MAX_LAT - MIN_LAT) / lat_steps

    for i in range(lng_steps):
        for j in range(lat_steps):
            center_lng = MIN_LNG + (i + 0.5) * lng_width
            center_lat = MIN_LAT + (j + 0.5) * lat_height

            # Distance-based density (denser near downtown SF ~37.79, -122.40)
            downtown_dist = math.sqrt((center_lng - (-122.40)) ** 2 + (center_lat - 37.79) ** 2)
            density_factor = math.exp(-downtown_dist * 30)  # exponential decay

            pop_density = 500 + density_factor * 14500 + random.uniform(-500, 500)
            pop_density = max(100, min(15000, pop_density))

            # Income: higher near marina/nob hill, lower in mission/tenderloin
            mission_dist = math.sqrt((center_lng - (-122.42)) ** 2 + (center_lat - 37.763) ** 2)
            marina_dist = math.sqrt((center_lng - (-122.437)) ** 2 + (center_lat - 37.803) ** 2)
            income_factor = 0.5 + 0.3 * (1 - math.exp(-marina_dist * 50)) + 0.2 * math.exp(-marina_dist * 40)
            median_income = 40000 + income_factor * 140000 + random.uniform(-10000, 10000)
            median_income = max(30000, min(200000, median_income))

            median_age = random.uniform(25, 55)
            population_total = int(pop_density * lng_width * lat_height * 111000 * 111000 / 1000000)
            population_total = max(1000, min(50000, population_total * random.uniform(0.8, 1.2)))

            # Add slight jitter to polygon boundaries for realism
            jitter = 0.001
            bl = [center_lng - lng_width/2 + random.uniform(-jitter, jitter),
                  center_lat - lat_height/2 + random.uniform(-jitter, jitter)]
            br = [center_lng + lng_width/2 + random.uniform(-jitter, jitter),
                  center_lat - lat_height/2 + random.uniform(-jitter, jitter)]
            tr = [center_lng + lng_width/2 + random.uniform(-jitter, jitter),
                  center_lat + lat_height/2 + random.uniform(-jitter, jitter)]
            tl = [center_lng - lng_width/2 + random.uniform(-jitter, jitter),
                  center_lat + lat_height/2 + random.uniform(-jitter, jitter)]
            coords = [[bl, br, tr, tl, bl]]  # properly closed

            features.append({
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": coords},
                "properties": {
                    "tract_id": tract_id,
                    "population_density": round(pop_density, 1),
                    "median_income": round(median_income, 0),
                    "median_age": round(median_age, 1),
                    "population_total": int(population_total),
                    "neighborhood": f"Tract-{tract_id}",
                }
            })
            tract_id += 1

    # Ensure we have exactly 50
    while len(features) < 50:
        center_lng = rand_lng()
        center_lat = rand_lat()
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": make_polygon_around(center_lng, center_lat, 0.01, 0.008),
            },
            "properties": {
                "tract_id": tract_id,
                "population_density": round(random.uniform(500, 8000), 1),
                "median_income": round(random.uniform(40000, 120000), 0),
                "median_age": round(random.uniform(28, 50), 1),
                "population_total": int(random.uniform(3000, 20000)),
                "neighborhood": f"Tract-{tract_id}",
            }
        })
        tract_id += 1

    return {"type": "FeatureCollection", "features": features[:50]}


# ─────────────────────────────────────────────
# 2. ROADS (200 LineString features)
# ─────────────────────────────────────────────

def generate_roads():
    features = []

    # Major SF highways (approximate routes within bbox)
    highways = [
        {
            "name": "US-101",
            "segments": [
                [[-122.397, 37.707], [-122.399, 37.720], [-122.400, 37.735], [-122.401, 37.750],
                 [-122.402, 37.765], [-122.403, 37.780], [-122.404, 37.795], [-122.405, 37.810]],
            ],
            "lanes": 6,
        },
        {
            "name": "I-280",
            "segments": [
                [[-122.420, 37.700], [-122.425, 37.715], [-122.430, 37.730], [-122.440, 37.745],
                 [-122.450, 37.755], [-122.460, 37.762], [-122.470, 37.768]],
            ],
            "lanes": 6,
        },
        {
            "name": "I-80",
            "segments": [
                [[-122.350, 37.815], [-122.360, 37.813], [-122.375, 37.810], [-122.390, 37.808],
                 [-122.405, 37.806], [-122.415, 37.805]],
            ],
            "lanes": 6,
        },
        {
            "name": "CA-1 (19th Ave)",
            "segments": [
                [[-122.475, 37.700], [-122.475, 37.715], [-122.474, 37.730], [-122.474, 37.745],
                 [-122.473, 37.760], [-122.473, 37.775], [-122.472, 37.790], [-122.471, 37.805]],
            ],
            "lanes": 4,
        },
    ]

    road_id = 1
    for hw in highways:
        for seg in hw["segments"]:
            features.append({
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": seg},
                "properties": {
                    "road_id": road_id,
                    "road_type": "highway",
                    "name": hw["name"],
                    "lanes": hw["lanes"],
                    "speed_kmh": 90,
                }
            })
            road_id += 1

    # Major arterials - SF grid streets
    arterials = [
        ("Market Street", [[-122.390, 37.793], [-122.400, 37.785], [-122.415, 37.775],
                           [-122.430, 37.765], [-122.445, 37.758]]),
        ("Mission Street", [[-122.390, 37.790], [-122.400, 37.782], [-122.415, 37.772],
                            [-122.430, 37.762], [-122.445, 37.752]]),
        ("Van Ness Ave", [[-122.422, 37.800], [-122.422, 37.790], [-122.422, 37.780],
                          [-122.422, 37.770], [-122.422, 37.760], [-122.422, 37.750]]),
        ("Geary Blvd", [[-122.400, 37.787], [-122.415, 37.784], [-122.430, 37.781],
                        [-122.445, 37.779], [-122.460, 37.777], [-122.475, 37.775]]),
        ("Cesar Chavez", [[-122.380, 37.749], [-122.395, 37.749], [-122.410, 37.749],
                          [-122.425, 37.749], [-122.440, 37.748]]),
        ("Embarcadero", [[-122.390, 37.793], [-122.389, 37.800], [-122.388, 37.808],
                         [-122.387, 37.815]]),
        ("Lombard Street", [[-122.400, 37.801], [-122.415, 37.802], [-122.430, 37.803],
                            [-122.445, 37.804]]),
        ("Bay Street", [[-122.400, 37.805], [-122.415, 37.805], [-122.430, 37.806],
                        [-122.445, 37.806]]),
        ("Divisadero St", [[-122.438, 37.800], [-122.437, 37.790], [-122.437, 37.780],
                           [-122.437, 37.770], [-122.436, 37.760]]),
        ("Potrero Ave", [[-122.407, 37.762], [-122.407, 37.752], [-122.407, 37.742],
                         [-122.407, 37.732]]),
    ]

    for name, coords in arterials:
        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {
                "road_id": road_id,
                "road_type": "arterial",
                "name": name,
                "lanes": random.randint(2, 4),
                "speed_kmh": 50,
            }
        })
        road_id += 1

    # Generate more arterials
    arterial_count = 40
    for i in range(arterial_count):
        start_lng = rand_lng()
        start_lat = rand_lat()
        direction = random.choice(["horizontal", "vertical", "diagonal"])

        if direction == "horizontal":
            coords = [[start_lng + j * 0.008, start_lat + random.uniform(-0.002, 0.002)]
                      for j in range(random.randint(3, 6))]
        elif direction == "vertical":
            coords = [[start_lng + random.uniform(-0.002, 0.002), start_lat + j * 0.008]
                      for j in range(random.randint(3, 6))]
        else:
            angle = random.uniform(0, math.pi)
            coords = [[start_lng + j * 0.008 * math.cos(angle),
                       start_lat + j * 0.006 * math.sin(angle)]
                      for j in range(random.randint(3, 5))]

        # Clip to bbox
        coords = [[max(MIN_LNG, min(MAX_LNG, c[0])), max(MIN_LAT, min(MAX_LAT, c[1]))]
                  for c in coords]

        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {
                "road_id": road_id,
                "road_type": "arterial",
                "name": f"Street-{road_id}",
                "lanes": random.randint(2, 4),
                "speed_kmh": 50,
            }
        })
        road_id += 1

    # Fill remainder with local streets
    while len(features) < 200:
        start_lng = rand_lng()
        start_lat = rand_lat()
        length = random.uniform(0.003, 0.015)
        angle = random.choice([0, math.pi/4, math.pi/2, 3*math.pi/4,
                               math.pi, 5*math.pi/4, 3*math.pi/2, 7*math.pi/4])
        n_pts = random.randint(2, 4)
        coords = []
        for k in range(n_pts):
            frac = k / (n_pts - 1) if n_pts > 1 else 0
            lng = max(MIN_LNG, min(MAX_LNG, start_lng + frac * length * math.cos(angle) * 1.3))
            lat = max(MIN_LAT, min(MAX_LAT, start_lat + frac * length * math.sin(angle)))
            coords.append([lng, lat])

        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {
                "road_id": road_id,
                "road_type": "local",
                "name": f"Local-{road_id}",
                "lanes": random.randint(1, 2),
                "speed_kmh": 30,
            }
        })
        road_id += 1

    return {"type": "FeatureCollection", "features": features[:200]}


# ─────────────────────────────────────────────
# 3. POI (300 Point features)
# ─────────────────────────────────────────────

POI_CLUSTERS = [
    # (center_lng, center_lat, label)
    (-122.398, 37.790, "downtown"),
    (-122.404, 37.779, "soma"),
    (-122.421, 37.762, "mission"),
    (-122.435, 37.762, "castro"),
    (-122.408, 37.800, "north_beach"),
    (-122.437, 37.803, "marina"),
    (-122.446, 37.769, "haight"),
    (-122.472, 37.778, "richmond"),
    (-122.414, 37.793, "nob_hill"),
    (-122.388, 37.793, "embarcadero"),
]

POI_CATEGORIES = [
    "retail", "restaurant", "cafe", "grocery", "gym",
    "pharmacy", "competitor_retail", "competitor_restaurant"
]

POI_NAMES = {
    "retail": ["Urban Outfitters", "Gap", "H&M", "Zara", "Nordstrom", "Target", "Macy's", "REI"],
    "restaurant": ["Burma Superstar", "Tartine Manufactory", "Zuni Cafe", "Delfina", "Nopa", "Foreign Cinema"],
    "cafe": ["Blue Bottle Coffee", "Philz Coffee", "Sightglass", "Ritual Coffee", "Four Barrel", "Verve"],
    "grocery": ["Safeway", "Whole Foods", "Rainbow Grocery", "Trader Joe's", "Lucky", "Mollie Stone's"],
    "gym": ["24 Hour Fitness", "Equinox", "Barry's", "Orange Theory", "SoulCycle", "CrossFit"],
    "pharmacy": ["Walgreens", "CVS", "Rite Aid", "Safeway Pharmacy", "Costco Pharmacy"],
    "competitor_retail": ["Amazon Go", "Walmart", "Costco", "Best Buy", "Home Depot", "Lowe's"],
    "competitor_restaurant": ["McDonald's", "Chipotle", "Subway", "Panera", "Shake Shack", "In-N-Out"],
}

def generate_poi():
    features = []
    poi_id = 1

    # Distribute 300 POIs across clusters
    per_cluster = 300 // len(POI_CLUSTERS)

    for cluster_lng, cluster_lat, cluster_label in POI_CLUSTERS:
        for _ in range(per_cluster):
            cat = random.choice(POI_CATEGORIES)
            names = POI_NAMES.get(cat, ["Unknown"])
            name = random.choice(names) + (f" #{random.randint(1,99)}" if random.random() > 0.5 else "")
            pt = biased_point(cluster_lng, cluster_lat, 0.01, 0.008)

            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": pt},
                "properties": {
                    "poi_id": poi_id,
                    "category": cat,
                    "name": name,
                    "rating": round(random.uniform(3.0, 5.0), 1),
                    "review_count": random.randint(10, 2000),
                    "cluster": cluster_label,
                }
            })
            poi_id += 1

    # Fill to 300
    while len(features) < 300:
        cat = random.choice(POI_CATEGORIES)
        names = POI_NAMES.get(cat, ["Unknown"])
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": rand_point()},
            "properties": {
                "poi_id": poi_id,
                "category": cat,
                "name": random.choice(names),
                "rating": round(random.uniform(3.0, 5.0), 1),
                "review_count": random.randint(5, 500),
                "cluster": "scattered",
            }
        })
        poi_id += 1

    return {"type": "FeatureCollection", "features": features[:300]}


# ─────────────────────────────────────────────
# 4. LAND USE (80 Polygon features)
# ─────────────────────────────────────────────

# SF zoning map approximate
ZONE_DISTRICTS = [
    # (center_lng, center_lat, zone_type, width, height)
    (-122.398, 37.793, "commercial", 0.018, 0.012),  # FiDi
    (-122.404, 37.779, "mixed", 0.016, 0.010),       # SoMa
    (-122.406, 37.787, "commercial", 0.008, 0.006),   # Union Square
    (-122.421, 37.763, "residential", 0.014, 0.010),  # Mission
    (-122.435, 37.762, "mixed", 0.010, 0.008),        # Castro
    (-122.414, 37.793, "residential", 0.010, 0.008),  # Nob Hill
    (-122.437, 37.803, "residential", 0.012, 0.008),  # Marina
    (-122.408, 37.800, "mixed", 0.010, 0.008),        # North Beach
    (-122.446, 37.769, "residential", 0.012, 0.010),  # Haight
    (-122.472, 37.778, "residential", 0.016, 0.012),  # Richmond
    (-122.411, 37.757, "industrial", 0.018, 0.010),   # Dogpatch/Potrero
    (-122.395, 37.762, "industrial", 0.012, 0.008),   # Bayview
    (-122.388, 37.800, "commercial", 0.010, 0.008),   # Embarcadero
    (-122.453, 37.752, "park", 0.020, 0.015),         # Golden Gate Park area
    (-122.462, 37.758, "park", 0.014, 0.012),         # Park
    (-122.413, 37.778, "institutional", 0.008, 0.006), # Civic Center
    (-122.458, 37.775, "residential", 0.012, 0.010),
    (-122.485, 37.754, "residential", 0.016, 0.012),  # Sunset
    (-122.400, 37.745, "industrial", 0.014, 0.008),
    (-122.420, 37.748, "mixed", 0.010, 0.008),
]

def generate_land_use():
    features = []
    zone_id = 1

    for center_lng, center_lat, zone_type, width, height in ZONE_DISTRICTS:
        # Main zone polygon
        area_sqm = width * height * 111000 * 111000  # approx in m²
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": make_polygon_around(center_lng, center_lat, width, height),
            },
            "properties": {
                "zone_id": zone_id,
                "zone_type": zone_type,
                "area_sqm": round(area_sqm, 0),
                "district": f"District-{zone_id}",
                "max_height_m": {"commercial": 120, "mixed": 60, "industrial": 30,
                                  "residential": 15, "park": 5, "institutional": 40}.get(zone_type, 20),
                "far": round(random.uniform(0.5, 8.0), 1),
            }
        })
        zone_id += 1

    # Fill to 80 with scattered zones
    zone_types = ["commercial", "residential", "industrial", "mixed", "park", "institutional"]
    zone_weights = [0.20, 0.35, 0.15, 0.15, 0.10, 0.05]

    while len(features) < 80:
        center_lng = rand_lng()
        center_lat = rand_lat()
        zone_type = random.choices(zone_types, weights=zone_weights)[0]
        width = random.uniform(0.005, 0.018)
        height = random.uniform(0.004, 0.014)
        area_sqm = width * height * 111000 * 111000

        # Use irregular polygon for variety
        coords = make_irregular_polygon(center_lng, center_lat, min(width, height) / 2)

        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": coords},
            "properties": {
                "zone_id": zone_id,
                "zone_type": zone_type,
                "area_sqm": round(area_sqm * random.uniform(0.5, 1.5), 0),
                "district": f"District-{zone_id}",
                "max_height_m": random.choice([10, 15, 20, 30, 40, 60, 90]),
                "far": round(random.uniform(0.5, 6.0), 1),
            }
        })
        zone_id += 1

    return {"type": "FeatureCollection", "features": features[:80]}


# ─────────────────────────────────────────────
# 5. ENVIRONMENTAL (60 Polygon features)
# ─────────────────────────────────────────────

ENVIRONMENTAL_ZONES = [
    # (center_lng, center_lat, risk_type, severity_range, width, height)
    (-122.390, 37.793, "air_quality_good", (0.1, 0.3), 0.020, 0.016),   # Downtown
    (-122.418, 37.770, "air_quality_moderate", (0.3, 0.6), 0.018, 0.014),
    (-122.390, 37.750, "air_quality_poor", (0.6, 0.9), 0.016, 0.010),   # Industrial area
    (-122.395, 37.800, "flood_zone", (0.5, 0.9), 0.010, 0.008),          # Near bay
    (-122.387, 37.808, "flood_zone", (0.6, 1.0), 0.008, 0.006),          # Shoreline
    (-122.400, 37.810, "low_flood", (0.2, 0.5), 0.012, 0.008),
    (-122.455, 37.760, "earthquake_high", (0.5, 0.9), 0.020, 0.016),     # Near fault line
    (-122.435, 37.745, "earthquake_high", (0.6, 0.8), 0.018, 0.014),
    (-122.415, 37.770, "earthquake_medium", (0.3, 0.6), 0.020, 0.016),
    (-122.480, 37.758, "earthquake_medium", (0.3, 0.5), 0.016, 0.012),
    (-122.420, 37.795, "air_quality_good", (0.1, 0.2), 0.014, 0.010),
    (-122.448, 37.780, "air_quality_moderate", (0.3, 0.5), 0.012, 0.010),
    (-122.406, 37.760, "low_flood", (0.2, 0.4), 0.014, 0.008),
    (-122.460, 37.800, "earthquake_medium", (0.2, 0.4), 0.016, 0.012),
    (-122.398, 37.775, "air_quality_good", (0.1, 0.3), 0.012, 0.010),
]

def generate_environmental():
    features = []
    env_id = 1

    for center_lng, center_lat, risk_type, sev_range, width, height in ENVIRONMENTAL_ZONES:
        severity = round(random.uniform(*sev_range), 2)
        area_sqm = width * height * 111000 * 111000

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": make_irregular_polygon(center_lng, center_lat, min(width, height) / 2, 8),
            },
            "properties": {
                "env_id": env_id,
                "risk_type": risk_type,
                "severity": severity,
                "area_sqm": round(area_sqm, 0),
                "description": {
                    "flood_zone": "FEMA 100-year flood zone",
                    "low_flood": "FEMA 500-year flood zone",
                    "earthquake_high": "High seismic hazard zone (Hayward Fault proximity)",
                    "earthquake_medium": "Moderate seismic hazard",
                    "air_quality_poor": "Non-attainment area, PM2.5 exceedance",
                    "air_quality_moderate": "Moderate air quality, occasional alerts",
                    "air_quality_good": "Attainment area, good air quality",
                }.get(risk_type, "Environmental zone"),
            }
        })
        env_id += 1

    # Fill to 60
    risk_types = ["flood_zone", "low_flood", "earthquake_high", "earthquake_medium",
                  "air_quality_good", "air_quality_moderate", "air_quality_poor"]
    risk_weights = [0.10, 0.10, 0.15, 0.15, 0.20, 0.20, 0.10]

    while len(features) < 60:
        risk_type = random.choices(risk_types, weights=risk_weights)[0]
        center_lng = rand_lng()
        center_lat = rand_lat()
        width = random.uniform(0.008, 0.020)
        height = random.uniform(0.006, 0.015)
        severity = round(random.uniform(0.1, 0.9), 2)

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": make_irregular_polygon(center_lng, center_lat, min(width, height) / 2, 6),
            },
            "properties": {
                "env_id": env_id,
                "risk_type": risk_type,
                "severity": severity,
                "area_sqm": round(width * height * 111000 * 111000, 0),
                "description": risk_type.replace("_", " ").title(),
            }
        })
        env_id += 1

    return {"type": "FeatureCollection", "features": features[:60]}


# ─────────────────────────────────────────────
# 6. COMPETITOR LOCATIONS (100 Point features)
# ─────────────────────────────────────────────

COMPETITOR_TYPES = [
    "retail_chain", "restaurant_chain", "grocery_chain", "pharmacy_chain",
    "fitness_chain", "electronics_chain", "home_improvement", "coffee_chain"
]

COMPETITOR_NAMES = {
    "retail_chain": ["Walmart", "Target", "Costco", "Amazon Go", "Dollar General", "Family Dollar"],
    "restaurant_chain": ["McDonald's", "Chipotle", "Subway", "Starbucks", "Panda Express", "Shake Shack"],
    "grocery_chain": ["Safeway", "Whole Foods", "Trader Joe's", "Lucky", "Kroger", "Aldi"],
    "pharmacy_chain": ["Walgreens", "CVS", "Rite Aid", "Walmart Pharmacy"],
    "fitness_chain": ["24 Hour Fitness", "Planet Fitness", "Equinox", "Gold's Gym"],
    "electronics_chain": ["Best Buy", "Apple Store", "Microsoft Store", "GameStop"],
    "home_improvement": ["Home Depot", "Lowe's", "Ace Hardware", "TrueValue"],
    "coffee_chain": ["Starbucks", "Peet's Coffee", "Dunkin'", "Dutch Bros"],
}

def generate_competitor_locations():
    features = []
    comp_id = 1

    # Concentrate competitors near high-traffic areas
    hotspots = [
        (-122.400, 37.787, 35),  # Downtown/Union Square
        (-122.404, 37.779, 25),  # SoMa
        (-122.421, 37.762, 20),  # Mission
        (-122.435, 37.762, 10),  # Castro
        (-122.437, 37.803, 10),  # Marina
    ]

    for center_lng, center_lat, count in hotspots:
        for _ in range(count):
            btype = random.choice(COMPETITOR_TYPES)
            names = COMPETITOR_NAMES[btype]
            pt = biased_point(center_lng, center_lat, 0.012, 0.010)
            revenue = round(random.uniform(500000, 10000000), 0)

            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": pt},
                "properties": {
                    "comp_id": comp_id,
                    "business_type": btype,
                    "name": random.choice(names),
                    "revenue_estimate": revenue,
                    "year_established": random.randint(1995, 2023),
                    "employee_count": random.randint(5, 500),
                    "rating": round(random.uniform(2.5, 4.8), 1),
                }
            })
            comp_id += 1

    # Fill to 100
    while len(features) < 100:
        btype = random.choice(COMPETITOR_TYPES)
        names = COMPETITOR_NAMES[btype]
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": rand_point()},
            "properties": {
                "comp_id": comp_id,
                "business_type": btype,
                "name": random.choice(names),
                "revenue_estimate": round(random.uniform(200000, 5000000), 0),
                "year_established": random.randint(1995, 2023),
                "employee_count": random.randint(5, 200),
                "rating": round(random.uniform(2.5, 4.5), 1),
            }
        })
        comp_id += 1

    return {"type": "FeatureCollection", "features": features[:100]}


# ─────────────────────────────────────────────
# MAIN - Generate all datasets
# ─────────────────────────────────────────────

def save_geojson(data, filename):
    path = DATA_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    count = len(data["features"])
    print(f"  ✓ {filename}: {count} features")


def main():
    print("Generating SF Bay Area GeoSpatial datasets...")
    print(f"  Bounding box: ({MIN_LNG}, {MIN_LAT}) -> ({MAX_LNG}, {MAX_LAT})")
    print()

    datasets = [
        ("demographic.geojson", generate_demographic),
        ("roads.geojson", generate_roads),
        ("poi.geojson", generate_poi),
        ("land_use.geojson", generate_land_use),
        ("environmental.geojson", generate_environmental),
        ("competitor_locations.geojson", generate_competitor_locations),
    ]

    for filename, generator in datasets:
        data = generator()
        save_geojson(data, filename)

    print()
    print("All datasets generated successfully!")
    print(f"  Output directory: {DATA_DIR.resolve()}")


if __name__ == "__main__":
    main()
