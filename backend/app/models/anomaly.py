from sqlalchemy import Column, String, Float, DateTime, Integer, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String, ForeignKey("scans.id"), nullable=False)

    anomaly_type = Column(String, nullable=False)  # structure, vegetation, thermal, movement
    severity = Column(String, default="medium")     # low, medium, high, critical

    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    bbox = Column(JSON, nullable=True)  # [x1, y1, x2, y2] in image coords

    confidence = Column(Float, default=0.0)
    description = Column(Text, nullable=True)
    ai_interpretation = Column(Text, nullable=True)

    # Detection metadata
    detected_by = Column(String, nullable=True)  # yolo, segment_anything, temporal
    object_class = Column(String, nullable=True)
    image_path = Column(String, nullable=True)
    thumbnail_path = Column(String, nullable=True)

    meta = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scan = relationship("Scan", back_populates="anomalies")
