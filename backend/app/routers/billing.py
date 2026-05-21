"""
Billing endpoints — plan upgrades via Stripe Checkout + webhook.
Works in mock mode if STRIPE_SECRET_KEY is not configured.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os

from app.database import get_db
from app.models.user import User
from app.models.organization import Organization, PlanTier
from app.utils.auth import get_current_user
from app.services.billing_service import create_checkout_session, current_usage
from app.utils.logger import logger

router = APIRouter(prefix="/billing", tags=["Billing"])


class UpgradeRequest(BaseModel):
    target_plan: str  # "pro" | "enterprise"
    success_url: str = "http://localhost:5173/billing/success"
    cancel_url: str = "http://localhost:5173/billing/cancel"


@router.post("/checkout")
async def start_checkout(
    body: UpgradeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.organization_id:
        raise HTTPException(400, "User has no organization")
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(404, "Organization not found")

    try:
        target = PlanTier(body.target_plan)
    except ValueError:
        raise HTTPException(400, f"Invalid plan: {body.target_plan}")

    if target == PlanTier.FREE:
        raise HTTPException(400, "Cannot checkout FREE — downgrade instead")

    session = await create_checkout_session(org, target, body.success_url, body.cancel_url)
    return session


@router.get("/usage")
async def get_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.organization_id:
        return {"organization": None, "usage": None}
    usage = await current_usage(db, current_user.organization_id)
    return {"organization_id": current_user.organization_id, "usage": usage}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Receives Stripe events: checkout.session.completed, invoice.payment_failed, etc."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        logger.warning("[BILLING] Webhook received but STRIPE_WEBHOOK_SECRET not set")
        return {"received": True, "verified": False}
    try:
        import stripe
        event = stripe.Webhook.construct_event(payload, sig, secret)
    except ImportError:
        raise HTTPException(500, "stripe SDK not installed")
    except Exception as e:
        raise HTTPException(400, f"Invalid webhook: {e}")

    etype = event["type"]
    data = event["data"]["object"]
    logger.info(f"[BILLING] Stripe event: {etype}")

    if etype == "checkout.session.completed":
        org_id = data.get("metadata", {}).get("org_id")
        plan = data.get("metadata", {}).get("target_plan")
        if org_id and plan:
            result = await db.execute(select(Organization).where(Organization.id == org_id))
            org = result.scalar_one_or_none()
            if org:
                org.plan = plan
                org.subscription_status = "active"
                org.stripe_customer_id = data.get("customer")
                await db.commit()
    elif etype in ("invoice.payment_failed", "customer.subscription.deleted"):
        customer_id = data.get("customer")
        if customer_id:
            result = await db.execute(
                select(Organization).where(Organization.stripe_customer_id == customer_id)
            )
            org = result.scalar_one_or_none()
            if org:
                org.subscription_status = (
                    "past_due" if etype == "invoice.payment_failed" else "cancelled"
                )
                await db.commit()
    return {"received": True, "type": etype}
