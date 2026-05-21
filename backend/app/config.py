from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "NEXUS ATLAS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "nexus-atlas-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    DATABASE_URL: str = "postgresql://nexus:nexus_pass@localhost:5432/nexus_atlas"

    REDIS_URL: str = "redis://localhost:6379"

    GEE_SERVICE_ACCOUNT: Optional[str] = None
    GEE_KEY_FILE: Optional[str] = None
    GEE_PROJECT: Optional[str] = None

    MAPBOX_TOKEN: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    UPLOAD_DIR: str = "./scans"
    REPORTS_DIR: str = "./reports"

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    RATE_LIMIT_PER_MINUTE: int = 60

    YOLO_MODEL_PATH: str = "./ai_models/weights/yolov8n.pt"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
