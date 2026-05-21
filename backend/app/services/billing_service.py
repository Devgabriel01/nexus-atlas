"""
Billing & usage enforcement.

Provides:
- `enforce_quota(org, kind)`: raises 402 if monthly quota exceeded
- `record_usage(org, user, kind, units)`: logs a UsageRecord
- `current_usage(org)`: returns this-month counters
- `create_checkout_session(org, plan)`: Stripe handoff (mock if no key)

Stripe is optional — when STRIPE_SECRET_KEY is unset, the service
returns mock checkout URLs so the rest of the app keeps working.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.organization import (
    Organization, UsageRecord, PlanTier, PLAN_LIMITS
)
from app.models.user import User
from app.utils.logger import logger


# ----------------------------------------------------------------------
# Quota
# ----------------------------------------------------------------------

KIND_TO_LIMIT_KEY = {
    "scan": "scans_per_month",
    "sar": "scans_per_month",
    "ai_query": "ai_queries_per_month",
}


async def current_usage(db: AsyncSession, org_id: str) -> dict:
    """Counters scoped to the current calendar month."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(UsageRecord.kind, func.count(UsageRecord.id))
        .where(and_(
            UsageRecord.organization_id == org_id,
            UsageRecord.created_at >= month_start,
        ))
        .group_by(UsageRecord.kind)
    )
    counts = {row[0]: row[1] for row in result.all()}
    return {
        "month_start": month_start.isoformat(),
        "scans": counts.get("scan", 0) + counts.get("sar", 0),
        "ai_queries": counts.get("ai_query", 0),
        "exports": counts.get("export", 0),
        "by_kind": counts,
    }


async def enforce_quota(db: AsyncSession, org: Organization, kind: str) -> None:
    """Raise HTTPException 402 if the org is over its monthly quota for this kind."""
    plan_limits = PLAN_LIMITS.get(PlanTier(org.plan), PLAN_LIMITS[PlanTier.FREE])
    usage = await current_usage(db, org.id)
    limit_key = KIND_TO_LIMIT_KEY.get(kind)
    if limit_key is None:
        return
    if kind == "sar" and not plan_limits.get("sar_enabled", False):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"error": "sar_not_in_plan",
                    "message": "SAR (Sentinel-1) requires PRO or ENTERPRISE plan.",
                    "upgrade_url": "/billing/upgrade"},
        )
    used = usage.get("scans" if kind in ("scan", "sar") else "ai_queries", 0)
    limit = plan_limits[limit_key]
    if used >= limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"error": "quota_exceeded",
                    "kind": kind,
                    "used": used,
                    "limit": limit,
                    "plan": org.plan,
                    "upgrade_url": "/billing/upgrade"},
        )


async def record_usage(
    db: AsyncSession,
    org_id: str,
    user_id: Optional[str],
    kind: str,
    units: float = 1.0,
    meta: Optional[dict] = None,
) -> None:
    rec = UsageRecord(
        organization_id=org_id, user_id=user_id, kind=kind,
        units=units, meta=meta,
    )
    db.add(rec)
    await db.flush()


# ----------------------------------------------------------------------
# Stripe (graceful no-op if not configured)
# ----------------------------------------------------------------------

def _stripe():
    import os
    key = os.environ.get("STRIPE_SECRET_KEY")
    if not key:
        return None
    try:
        import stripe
        stripe.api_key = key
        return stripe
    except ImportError:
        logger.warning("[BILLING] stripe SDK not installed")
        return None


async def create_checkout_session(
    org: Organization, target_plan: PlanTier, success_url: str, cancel_url: str
) -> dict:
    stripe = _stripe()
    if not stripe:
        return {
            "url": f"{success_url}?mock=true&plan={target_plan.value}",
            "mock": True,
            "message": "Stripe not configured. In production set STRIPE_SECRET_KEY.",
        }
    price_lookup = {
        PlanTier.PRO: "price_pro_monthly",         # configure in Stripe Dashboard
        PlanTier.ENTERPRISE: "price_enterprise_monthly",
    }
    try:
        session = stripe.checkout.Session.create(
            customer=org.stripe_customer_id,
            mode="subscription",
            line_items=[{"price": price_lookup[target_plan], "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"org_id": org.id, "target_plan": target_plan.value},
        )
        return {"url": session.url, "session_id": session.id, "mock": False}
    except Exception as e:
        logger.error(f"[BILLING] Stripe checkout failed: {e}")
        raise HTTPException(500, "Could not create checkout session")
