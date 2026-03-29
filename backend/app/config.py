from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "GeoSpatial Site Readiness Analyzer"
    data_dir: str = "data"
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
