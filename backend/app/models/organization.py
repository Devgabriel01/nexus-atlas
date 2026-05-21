"""
Multi-tenancy core models — organizations, plans, subscriptions, usage records.

Design:
- An Organization is the billing unit. Users belong to one Org (owner relationship).
- Org has a Plan (FREE / PRO / ENTERPRISE) with monthly quotas.
- UsageRecord tracks each scan/AI call for billing and quota enforcement.
- Subscription holds payment status (active / past_due / cancelled).
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class PlanTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


PLAN_LIMITS = {
    PlanTier.FREE: {
        "scans_per_month": 25,
        "ai_queries_per_month": 100,
        "max_region_km2": 10_000,
        "sar_enabled": False,
        "price_usd_month": 0,
    },
    PlanTier.PRO: {
        "scans_per_month": 500,
        "ai_queries_per_month": 5_000,
        "max_region_km2": 100_000,
        "sar_enabled": True,
        "price_usd_month": 49,
    },
    PlanTier.ENTERPRISE: {
        "scans_per_month": 1_000_000,
        "ai_queries_per_month": 1_000_000,
        "max_region_km2": 10_000_000,
        "sar_enabled": True,
        "price_usd_month": 499,
    },
}


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    plan = Column(String, default=PlanTier.FREE)

    # Billing
    stripe_customer_id = Column(String, nullable=True)
    subscription_status = Column(String, default="trial")  # trial|active|past_due|cancelled
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)

    owner_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    settings = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="organization",
                         foreign_keys="User.organization_id")
    usage_records = relationship("UsageRecord", back_populates="organization",
                                 cascade="all, delete-orphan")


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    kind = Column(String, nullable=False, index=True)  # scan|ai_query|sar|export
    units = Column(Float, default=1.0)  # cost in abstract units
    meta = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    organization = relationship("Organization", back_populates="usage_records")
