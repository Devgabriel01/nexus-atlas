from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.scan import Scan, ScanStatus
from app.schemas.scan import ScanCreate, ScanResponse, ScanStatusResponse
from app.utils.auth import get_current_user
from app.services.scan_service import run_full_scan
from app.services.billing_service import enforce_quota, record_usage
from app.models.organization import Organization
from app.utils.logger import logger

router = APIRouter(prefix="/scan", tags=["Scanning"])


@router.post("/", response_model=ScanResponse, status_code=202)
async def create_scan(
    data: ScanCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Multi-tenancy: enforce quota if user belongs to an org
    if current_user.organization_id:
        org_result = await db.execute(
            select(Organization).where(Organization.id == current_user.organization_id)
        )
        org = org_result.scalar_one_or_none()
        if org:
            kind = "sar" if "sar" in str(data.scan_type).lower() else "scan"
            await enforce_quota(db, org, kind)
            await record_usage(db, org.id, current_user.id, kind,
                               meta={"name": data.name})

    scan = Scan(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        lat_min=data.lat_min,
        lat_max=data.lat_max,
        lon_min=data.lon_min,
        lon_max=data.lon_max,
        center_lat=(data.lat_min + data.lat_max) / 2,
        center_lon=(data.lon_min + data.lon_max) / 2,
        scan_type=data.scan_type,
        date_start=data.date_start,
        date_end=data.date_end,
        status=ScanStatus.PENDING,
    )
    db.add(scan)
    await db.flush()
    await db.refresh(scan)

    logger.info(f"Scan {scan.id} created by {current_user.username}")
    background_tasks.add_task(run_full_scan, scan.id)

    return ScanResponse.model_validate(scan)


@router.get("/", response_model=List[ScanResponse])
async def list_scans(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Scan)
        .where(Scan.user_id == current_user.id)
        .order_by(desc(Scan.created_at))
        .offset(skip)
        .limit(limit)
    )
    return [ScanResponse.model_validate(s) for s in result.scalars().all()]


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan or scan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Scan not found")
    return ScanResponse.model_validate(scan)


@router.get("/{scan_id}/status", response_model=ScanStatusResponse)
async def get_scan_status(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan or scan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Scan not found")

    progress_map = {
        ScanStatus.PENDING: 0,
        ScanStatus.PROCESSING: 50,
        ScanStatus.COMPLETED: 100,
        ScanStatus.FAILED: 0,
    }
    return ScanStatusResponse(
        id=scan.id,
        status=scan.status,
        progress=progress_map.get(scan.status, 0),
        message=f"Scan {scan.status}",
        anomaly_count=scan.anomaly_count,
    )


@router.delete("/{scan_id}", status_code=204)
async def delete_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan or scan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Scan not found")
    await db.delete(scan)
