from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
from pathlib import Path
from app.database import get_db
from app.models.user import User
from app.models.report import Report
from app.models.scan import Scan
from app.schemas.report import ReportCreate, ReportResponse
from app.utils.auth import get_current_user
from app.services.report_service import generate_report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/", response_model=ReportResponse, status_code=201)
async def create_report(
    data: ReportCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Scan).where(Scan.id == data.scan_id))
    scan = result.scalar_one_or_none()
    if not scan or scan.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Scan not found")

    report = Report(
        scan_id=data.scan_id,
        user_id=current_user.id,
        title=data.title,
        summary=data.summary,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)

    background_tasks.add_task(generate_report, report.id)
    return ReportResponse.model_validate(report)


@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Report)
        .where(Report.user_id == current_user.id)
        .order_by(desc(Report.created_at))
    )
    return [ReportResponse.model_validate(r) for r in result.scalars().all()]


@router.get("/{report_id}/download/pdf")
async def download_pdf(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == current_user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.pdf_path or not Path(report.pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF not ready yet")
    return FileResponse(report.pdf_path, media_type="application/pdf", filename=f"report_{report_id}.pdf")


@router.get("/{report_id}/download/json")
async def download_json(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == current_user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.json_path or not Path(report.json_path).exists():
        raise HTTPException(status_code=404, detail="JSON export not ready yet")
    return FileResponse(report.json_path, media_type="application/json", filename=f"report_{report_id}.json")
