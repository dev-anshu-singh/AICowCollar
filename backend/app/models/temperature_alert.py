from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..database import Base

class TemperatureAlert(Base):
    """
    Stores historical health alerts triggered by the CUSUM temperature monitoring engine
    (e.g., suspected fever from mastitis/BRD, or hypothermia from milk fever).
    """
    __tablename__ = "temperature_alerts"

    id = Column(Integer, primary_key=True, index=True)
    cow_id = Column(Integer, ForeignKey("cows.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Alert Category: SUSPECTED_FEVER, SUSPECTED_HYPOTHERMIA
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), default="WARNING")  # INFO, WARNING, CRITICAL
    
    # Thermal Metrics at Trigger Time
    current_temp = Column(Float, nullable=False)
    baseline_temp = Column(Float, nullable=False)
    temp_delta = Column(Float, nullable=False)
    cusum_score = Column(Float, nullable=False)
    
    # Clinical explanation for the farmer/veterinarian
    clinical_notes = Column(String(255), nullable=False)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    cow = relationship("Cow", back_populates="temperature_alerts")

    @property
    def tag_id(self) -> str:
        return self.cow.tag_id if self.cow else ""
