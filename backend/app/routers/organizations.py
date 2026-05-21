"""
Organization & multi-tenancy endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import re

from app.database import get_db
from app.models.user import User
from app.models.organization import Organization, PlanTier, PLAN_LIMITS
from app.utils.auth import get_current_user
from app.services.billing_service import current_usage

router = APIRouter(prefix="/orgs", tags=["Organizations"])


class OrgCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)


class OrgResponse(BaseModel):
    id: str
    name: str
    slug: str
    plan: str
    subscription_status: str

    class Config:
        from_attributes = True


def _slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9\s-]", "", s).strip().lower()
    return re.sub(r"[\s-]+", "-", s)[:60]


@router.post("/", response_model=OrgResponse, status_code=201)
async def create_org(
    data: OrgCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    slug = _slugify(data.name)
    # Ensure unique slug
    existing = await db.execute(select(Organization).where(Organization.slug == slug))
    if existing.scalar_one_or_none():
        slug = f"{slug}-{current_user.id[:6]}"

    org = Organization(
        name=data.name, slug=slug,
        owner_user_id=current_user.id,
        plan=PlanTier.FREE.value,
        subscription_status="trial",
    )
    db.add(org)
    await db.flush()

    current_user.organization_id = org.id
    await db.flush()
    await db.refresh(org)
    return OrgResponse.model_validate(org)


@router.get("/me")
async def my_org(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.organization_id:
        return {"organization": None}
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        return {"organization": None}
    usage = await current_usage(db, org.id)
    limits = PLAN_LIMITS[PlanTier(org.plan)]
    return {
        "organization": OrgResponse.model_validate(org).model_dump(),
        "limits": limits,
        "usage": usage,
    }


@router.get("/plans")
async def list_plans() -> List[dict]:
    return [
        {"tier": tier.value, **limits, "name": tier.value.upper()}
        for tier, limits in PLAN_LIMITS.items()
    ]
