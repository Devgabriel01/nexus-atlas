from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Dict, Any
from app.database import get_db
from app.models.user import User
from app.models.scan import Scan
from app.models.anomaly import Anomaly
from app.utils.auth import get_current_user

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/")
async def get_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(30, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    result = await db.execute(
        select(Scan)
        .where(Scan.user_id == current_user.id)
        .order_by(desc(Scan.created_at))
        .offset(skip)
        .limit(limit)
    )
    scans = result.scalars().all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "scan_type": s.scan_type,
            "status": s.status,
            "anomaly_count": s.anomaly_count,
            "confidence_score": s.confidence_score,
            "created_at": s.created_at.isoformat(),
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            "center": {"lat": s.center_lat, "lon": s.center_lon},
        }
        for s in scans
    ]
