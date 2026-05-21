from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.anomaly import Anomaly
from app.models.scan import Scan
from app.schemas.scan import AnomalyResponse
from app.utils.auth import get_current_user

router = APIRouter(prefix="/anomalies", tags=["Anomalies"])


@router.get("/", response_model=List[AnomalyResponse])
async def list_anomalies(
    scan_id: Optional[str] = None,
    severity: Optional[str] = None,
    anomaly_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(Anomaly)
        .join(Scan)
        .where(Scan.user_id == current_user.id)
        .order_by(desc(Anomaly.created_at))
    )

    if scan_id:
        query = query.where(Anomaly.scan_id == scan_id)
    if severity:
        query = query.where(Anomaly.severity == severity)
    if anomaly_type:
        query = query.where(Anomaly.anomaly_type == anomaly_type)

    result = await db.execute(query.offset(skip).limit(limit))
    return [AnomalyResponse.model_validate(a) for a in result.scalars().all()]


@router.get("/{anomaly_id}", response_model=AnomalyResponse)
async def get_anomaly(
    anomaly_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Anomaly).join(Scan).where(
            Anomaly.id == anomaly_id, Scan.user_id == current_user.id
        )
    )
    anomaly = result.scalar_one_or_none()
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return AnomalyResponse.model_validate(anomaly)
