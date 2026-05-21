from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.scan import ScanStatus, ScanType


class ScanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    lat_min: float = Field(..., ge=-90, le=90)
    lat_max: float = Field(..., ge=-90, le=90)
    lon_min: float = Field(..., ge=-180, le=180)
    lon_max: float = Field(..., ge=-180, le=180)
    scan_type: ScanType = ScanType.FULL
    date_start: Optional[str] = None
    date_end: Optional[str] = None


class AnomalyResponse(BaseModel):
    id: str
    anomaly_type: str
    severity: str
    latitude: float
    longitude: float
    confidence: float
    description: Optional[str]
    ai_interpretation: Optional[str]
    detected_by: Optional[str]
    object_class: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ScanResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    scan_type: str
    status: str
    date_start: Optional[str]
    date_end: Optional[str]
    anomaly_count: int
    confidence_score: float
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScanStatusResponse(BaseModel):
    id: str
    status: str
    progress: int = 0
    message: str = ""
    anomaly_count: int = 0
