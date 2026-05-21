from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user
from app.services.ai_service import get_ai_service

router = APIRouter(prefix="/analyze", tags=["Analysis"])


class CoordinateAnalysisRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(10.0, ge=0.1, le=500.0)


class NDVIRequest(BaseModel):
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    date_start: str = "2023-01-01"
    date_end: str = "2024-01-01"


class AIQueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000)
    context: Optional[str] = Field(default="", max_length=8000)


@router.post("/coordinates")
async def analyze_coordinates(
    data: CoordinateAnalysisRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Quick analysis of a single coordinate point. Adds AI readout if Groq is online."""
    terrain = _classify_terrain(data.latitude, data.longitude)
    risk = _assess_risk_factors(data.latitude, data.longitude)

    payload: Dict[str, Any] = {
        "latitude": data.latitude,
        "longitude": data.longitude,
        "radius_km": data.radius_km,
        "terrain_type": terrain,
        "risk_factors": risk,
        "recommended_scan_type": "full",
        "estimated_scan_time_seconds": 45,
        "ai_readout": None,
    }

    ai = get_ai_service()
    if ai.is_configured:
        try:
            readout = await ai.interpret_coordinate(
                data.latitude, data.longitude, data.radius_km, terrain, risk
            )
            payload["ai_readout"] = readout
        except Exception:
            pass
    return payload


@router.post("/ndvi")
async def analyze_ndvi(
    data: NDVIRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Calculate NDVI for a region (requires Earth Engine; mock fallback otherwise)."""
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "geospatial"))
        from ndvi import NDVIAnalyzer
        analyzer = NDVIAnalyzer()
        result = analyzer.compute(
            lat_min=data.lat_min, lat_max=data.lat_max,
            lon_min=data.lon_min, lon_max=data.lon_max,
            date_start=data.date_start, date_end=data.date_end,
        )
        return result
    except Exception as e:
        return {"error": str(e), "ndvi_mean": 0.0, "ndvi_min": 0.0, "ndvi_max": 0.0}


@router.post("/ai-query")
async def ai_query(
    data: AIQueryRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Free-form natural-language query for the dashboard console terminal."""
    ai = get_ai_service()
    if not ai.is_configured:
        raise HTTPException(
            status_code=503,
            detail="AI service not configured. Set GROQ_API_KEY in backend/.env.",
        )
    answer = await ai.free_query(data.question, data.context or "")
    if answer is None:
        raise HTTPException(status_code=502, detail="AI provider returned no response")
    return {
        "question": data.question,
        "answer": answer,
        "model": ai.model,
        "provider": "groq",
    }


@router.get("/ai/status")
async def ai_status() -> Dict[str, Any]:
    """Public status endpoint — surfaces which AI provider is wired up."""
    return get_ai_service().status


def _classify_terrain(lat: float, lon: float) -> str:
    if abs(lat) > 60:
        return "polar"
    if abs(lat) < 23.5:
        return "tropical"
    return "temperate"


def _assess_risk_factors(lat: float, lon: float) -> List[str]:
    factors = []
    if abs(lat) < 30:
        factors.append("high_solar_radiation")
    if abs(lat) > 50:
        factors.append("seasonal_snow_cover")
    return factors or ["nominal"]
