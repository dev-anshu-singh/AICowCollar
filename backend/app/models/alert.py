from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..database import Base

class ActivityAlert(Base):
    __tablename__ = "activity_alerts"

    id = Column(Integer, primary_key=True, index=True)
    cow_id = Column(Integer, ForeignKey("cows.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # Alert Classification: FEEDING_DEFICIT, ESTRUS_RESTLESSNESS, EXCESSIVE_LYING_LAMENESS, NORMAL
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), default="WARNING")  # INFO, WARNING, CRITICAL
    
    # Metric Shift Details
    eating_change_pct = Column(Float, nullable=True)
    walking_change_pct = Column(Float, nullable=True)
    lying_change_pct = Column(Float, nullable=True)
    
    # Context
    baseline_eating_hours = Column(Float, nullable=True)
    current_eating_hours = Column(Float, nullable=True)
    baseline_walking_hours = Column(Float, nullable=True)
    current_walking_hours = Column(Float, nullable=True)
    baseline_lying_hours = Column(Float, nullable=True)
    current_lying_hours = Column(Float, nullable=True)
    
    # Plain English Message
    message = Column(String(255), nullable=False)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    cow = relationship("Cow", back_populates="alerts")
