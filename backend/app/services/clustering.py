"""Spatial clustering and hot-spot detection using H3 and DBSCAN."""
import numpy as np
import h3
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from app.services.scoring import compute_site_score
from app.models.schemas import ScoreRequest, HotspotAnalysis, LayerWeights, H3Cell, Cluster


def generate_hotspot_analysis(
    bbox: tuple,
    use_case: str = "retail",
    weights: LayerWeights = None,
    h3_resolution: int = 8,
) -> HotspotAnalysis:
    """Generate H3 hexagonal binning hot-spot analysis over bbox."""
    min_lng, min_lat, max_lng, max_lat = bbox

    # h3 v4 uses h3shape_to_cells / LatLngPoly; v3 uses polyfill_geojson
    if hasattr(h3, 'h3shape_to_cells'):
        poly = h3.LatLngPoly([
            (min_lat, min_lng),
            (max_lat, min_lng),
            (max_lat, max_lng),
            (min_lat, max_lng),
        ])
        h3_cells_set = h3.h3shape_to_cells(poly, h3_resolution)
    else:
        polygon = {
            "type": "Polygon",
            "coordinates": [[
                [min_lng, min_lat],
                [max_lng, min_lat],
                [max_lng, max_lat],
                [min_lng, max_lat],
                [min_lng, min_lat],
            ]],
        }
        h3_cells_set = h3.polyfill_geojson(polygon, h3_resolution)

    if not h3_cells_set:
        return HotspotAnalysis(h3_cells=[], clusters=[])

    cell_data = []
    for cell in h3_cells_set:
        # h3 v4: cell_to_latlng; v3: h3_to_geo
        if hasattr(h3, 'cell_to_latlng'):
            centroid = h3.cell_to_latlng(cell)  # (lat, lng)
        else:
            centroid = h3.h3_to_geo(cell)  # (lat, lng)
        lat, lng = centroid

        try:
            req = ScoreRequest(
                lat=lat,
                lng=lng,
                use_case=use_case,
                weights=weights or LayerWeights(),
                radius_km=0.5,
            )
            result = compute_site_score(req)
            cell_data.append({
                "h3_index": cell,
                "score": result.composite_score,
                "centroid_lat": lat,
                "centroid_lng": lng,
                "cluster_id": -1,
            })
        except Exception:
            continue

    if not cell_data:
        return HotspotAnalysis(h3_cells=[], clusters=[])

    # DBSCAN clustering on cells
    coords = np.array([[d["centroid_lat"], d["centroid_lng"]] for d in cell_data])
    scores = np.array([d["score"] for d in cell_data])

    scaler = StandardScaler()
    features = scaler.fit_transform(
        np.column_stack([coords, scores.reshape(-1, 1)])
    )

    db = DBSCAN(eps=0.3, min_samples=2).fit(features)
    labels = db.labels_

    for i, d in enumerate(cell_data):
        d["cluster_id"] = int(labels[i])

    # Summarize clusters
    clusters_out = []
    unique_labels = set(labels) - {-1}
    for label in unique_labels:
        cluster_cells = [d for i, d in enumerate(cell_data) if labels[i] == label]
        avg_score = float(np.mean([c["score"] for c in cluster_cells]))
        center_lat = float(np.mean([c["centroid_lat"] for c in cluster_cells]))
        center_lng = float(np.mean([c["centroid_lng"] for c in cluster_cells]))
        size = int(np.sum(labels == label))

        classification = (
            "hot" if avg_score >= 70
            else ("warm" if avg_score >= 50 else "cold")
        )

        clusters_out.append(
            Cluster(
                cluster_id=int(label),
                centroid=[center_lat, center_lng],
                size=size,
                avg_score=round(avg_score, 1),
                classification=classification,
            )
        )

    h3_cells_models = [
        H3Cell(
            h3_index=d["h3_index"],
            score=d["score"],
            centroid_lat=d["centroid_lat"],
            centroid_lng=d["centroid_lng"],
            cluster_id=d["cluster_id"],
        )
        for d in cell_data
    ]

    return HotspotAnalysis(h3_cells=h3_cells_models, clusters=clusters_out)
