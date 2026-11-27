from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, String, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..database import Base

class HeartRateRecord(Base):
    """
    Stores heart rate telemetry readings along with deviation from baseline.
    """
    __tablename__ = "heart_rate_records"

    id = Column(Integer, primary_key=True, index=True)
    cow_id = Column(Integer, ForeignKey("cows.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Pulse measurements (BPM)
    heart_rate = Column(Float, nullable=False)
    baseline_bpm = Column(Float, nullable=False, default=65.0)
    delta_bpm = Column(Float, nullable=False, default=0.0)      # (heart_rate - baseline_bpm)
    delta_pct = Column(Float, nullable=False, default=0.0)      # % change from baseline
    
    # Status: NORMAL, HIGH_HEART_RATE, LOW_HEART_RATE
    status = Column(String(50), nullable=False, default="NORMAL")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    cow = relationship("Cow", back_populates="heart_rate_records")

    @property
    def tag_id(self) -> str:
        return self.cow.tag_id if self.cow else ""


class HeartRateAlert(Base):
    """
    Stores health anomaly alerts triggered by the Heart Rate service.
    """
    __tablename__ = "heart_rate_alerts"

    id = Column(Integer, primary_key=True, index=True)
    cow_id = Column(Integer, ForeignKey("cows.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Alert Type: HIGH_HEART_RATE, LOW_HEART_RATE
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), default="WARNING")  # WARNING, CRITICAL
    
    current_bpm = Column(Float, nullable=False)
    baseline_bpm = Column(Float, nullable=False)
    delta_pct = Column(Float, nullable=False)
    
    clinical_notes = Column(String(255), nullable=False)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    cow = relationship("Cow", back_populates="heart_rate_alerts")

    @property
    def tag_id(self) -> str:
        return self.cow.tag_id if self.cow else ""
