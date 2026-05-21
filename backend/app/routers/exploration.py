from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any
from app.database import get_db
from app.models.user import User
from app.models.report import Region
from app.utils.auth import get_current_user

router = APIRouter(prefix="/exploration", tags=["Exploration"])


@router.get("/suggested-regions")
async def get_suggested_regions(
    category: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Return pre-loaded regions of interest for exploration."""
    query = select(Region)
    if category:
        query = query.where(Region.category == category)
    result = await db.execute(query.limit(20))
    regions = result.scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "category": r.category,
            "bounds": {
                "lat_min": r.lat_min, "lat_max": r.lat_max,
                "lon_min": r.lon_min, "lon_max": r.lon_max,
            },
            "watch_level": r.watch_level,
        }
        for r in regions
    ]


@router.get("/heatmap-data")
async def get_heatmap_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return aggregated anomaly positions for the global heatmap."""
    from app.models.anomaly import Anomaly
    from app.models.scan import Scan
    result = await db.execute(
        select(Anomaly.latitude, Anomaly.longitude, Anomaly.severity)
        .join(Scan)
        .where(Scan.user_id == current_user.id)
        .limit(500)
    )
    rows = result.all()
    points = [
        {"lat": r.latitude, "lon": r.longitude, "weight": {"low": 0.3, "medium": 0.6, "high": 0.9, "critical": 1.0}.get(r.severity, 0.5)}
        for r in rows
    ]
    return {"points": points, "total": len(points)}


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    from app.models.scan import Scan, ScanStatus
    from app.models.anomaly import Anomaly
    from sqlalchemy import func

    scan_count = await db.scalar(select(func.count()).where(Scan.user_id == current_user.id))
    anomaly_count = await db.scalar(
        select(func.count()).select_from(Anomaly).join(Scan).where(Scan.user_id == current_user.id)
    )
    critical_count = await db.scalar(
        select(func.count()).select_from(Anomaly).join(Scan)
        .where(Scan.user_id == current_user.id, Anomaly.severity == "critical")
    )
    return {
        "total_scans": scan_count or 0,
        "total_anomalies": anomaly_count or 0,
        "critical_anomalies": critical_count or 0,
        "regions_monitored": scan_count or 0,
    }
