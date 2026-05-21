from sqlalchemy import Column, String, Float, DateTime, Integer, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String, ForeignKey("scans.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    full_analysis = Column(Text, nullable=True)

    threat_level = Column(String, default="low")  # low, medium, high, critical
    anomaly_summary = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)

    # Export paths
    pdf_path = Column(String, nullable=True)
    json_path = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scan = relationship("Scan", back_populates="reports")
    user = relationship("User", back_populates="reports")


class Region(Base):
    __tablename__ = "regions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)  # arctic, forest, urban, ocean, desert

    lat_min = Column(Float, nullable=False)
    lat_max = Column(Float, nullable=False)
    lon_min = Column(Float, nullable=False)
    lon_max = Column(Float, nullable=False)

    watch_level = Column(String, default="normal")
    meta = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
