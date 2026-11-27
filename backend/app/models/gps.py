from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, String, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..database import Base

class GPSRecord(Base):
    """
    Stores individual GPS location telemetry records, trajectory metrics,
    and GMM-classified behavioral state (Resting, Grazing, Walking).
    """
    __tablename__ = "gps_records"

    id = Column(Integer, primary_key=True, index=True)
    cow_id = Column(Integer, ForeignKey("cows.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)

    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    ttf_ms = Column(Float, nullable=True, default=1000.0)

    # Derived trajectory & classification metrics
    speed_mps = Column(Float, nullable=True)
    gps_behavior = Column(String(50), nullable=False, default="Unknown")  # Resting, Grazing, Walking
    is_outside = Column(Boolean, nullable=False, default=False)
    geofence_breach = Column(Boolean, nullable=False, default=False)
    alert_message = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    cow = relationship("Cow", back_populates="gps_records")

    @property
    def tag_id(self) -> str:
        return self.cow.tag_id if self.cow else ""


class GPSAlert(Base):
    """
    Stores geofence perimeter breach alerts (2-strike debounced).
    """
    __tablename__ = "gps_alerts"

    id = Column(Integer, primary_key=True, index=True)
    cow_id = Column(Integer, ForeignKey("cows.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)

    alert_type = Column(String(50), nullable=False, default="GEOFENCE_BREACH")
    severity = Column(String(20), default="CRITICAL")  # WARNING, CRITICAL

    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    message = Column(String(255), nullable=False)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    cow = relationship("Cow", back_populates="gps_alerts")

    @property
    def tag_id(self) -> str:
        return self.cow.tag_id if self.cow else ""
