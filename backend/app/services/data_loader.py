"""Loads and caches geospatial data layers."""
import geopandas as gpd
from pathlib import Path
from app.config import settings


class DataLoader:
    _cache: dict = {}

    @classmethod
    def load_layer(cls, layer_name: str) -> gpd.GeoDataFrame:
        if layer_name not in cls._cache:
            path = Path(settings.data_dir) / f"{layer_name}.geojson"
            if not path.exists():
                raise FileNotFoundError(
                    f"Layer file not found: {path}. "
                    "Run 'python generate_data.py' first."
                )
            gdf = gpd.read_file(str(path))
            if gdf.crs is None:
                gdf = gdf.set_crs(epsg=4326)
            cls._cache[layer_name] = gdf
        return cls._cache[layer_name]

    @classmethod
    def get_all_layers(cls) -> dict:
        layers = [
            "demographic",
            "roads",
            "poi",
            "land_use",
            "environmental",
            "competitor_locations",
        ]
        return {name: cls.load_layer(name) for name in layers}

    @classmethod
    def clear_cache(cls):
        cls._cache = {}


data_loader = DataLoader()
