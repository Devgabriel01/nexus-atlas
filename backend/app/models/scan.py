from sqlalchemy import Column, String, Float, DateTime, Integer, JSON, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanType(str, enum.Enum):
    TEMPORAL = "temporal"
    ANOMALY = "anomaly"
    NDVI = "ndvi"
    STRUCTURE = "structure"
    SAR = "sar"           # Sentinel-1 radar (cloud-penetrating)
    FULL_SAR = "full_sar"  # everything + SAR
    FULL = "full"


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Geographic bounds
    lat_min = Column(Float, nullable=False)
    lat_max = Column(Float, nullable=False)
    lon_min = Column(Float, nullable=False)
    lon_max = Column(Float, nullable=False)
    center_lat = Column(Float, nullable=True)
    center_lon = Column(Float, nullable=True)

    scan_type = Column(String, default=ScanType.FULL)
    status = Column(String, default=ScanStatus.PENDING)

    # Time range for temporal analysis
    date_start = Column(String, nullable=True)
    date_end = Column(String, nullable=True)

    # Results
    anomaly_count = Column(Integer, default=0)
    confidence_score = Column(Float, default=0.0)
    meta = Column("metadata", JSON, nullable=True)

    # File paths
    image_before = Column(String, nullable=True)
    image_after = Column(String, nullable=True)
    heatmap_path = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="scans")
    anomalies = relationship("Anomaly", back_populates="scan", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="scan")
