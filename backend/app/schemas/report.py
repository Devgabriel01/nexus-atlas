from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ReportCreate(BaseModel):
    scan_id: str
    title: str
    summary: Optional[str] = None


class ReportResponse(BaseModel):
    id: str
    scan_id: str
    title: str
    summary: Optional[str]
    full_analysis: Optional[str]
    threat_level: str
    anomaly_summary: Optional[Dict[str, Any]]
    recommendations: Optional[List[str]]
    pdf_path: Optional[str]
    json_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
