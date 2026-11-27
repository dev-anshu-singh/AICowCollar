from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..database import Base

class TemperatureRecord(Base):
    """
    Stores 10-minute or hourly temperature telemetry readings along with
    the ambient correction, diurnal residual, and real-time CUSUM statistics.
    """
    __tablename__ = "temperature_records"

    id = Column(Integer, primary_key=True, index=True)
    cow_id = Column(Integer, ForeignKey("cows.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Raw sensor measurements (°C)
    skin_temperature = Column(Float, nullable=False)
    ambient_temperature = Column(Float, nullable=True, default=22.0)
    
    # Processed measurements
    corrected_temperature = Column(Float, nullable=False)    # Decoupled from ambient heat/cold
    expected_baseline_temp = Column(Float, nullable=False)   # Cow's diurnal expected baseline for this hour
    residual_delta = Column(Float, nullable=False)           # (corrected_temp - baseline_temp)
    
    # CUSUM Cumulative State
    cusum_positive = Column(Float, nullable=False, default=0.0)  # S_t^+ for fever detection
    cusum_negative = Column(Float, nullable=False, default=0.0)  # S_t^- for hypothermia detection
    
    # Real-time state classification: NORMAL, SUSPECTED_FEVER, SUSPECTED_HYPOTHERMIA
    status = Column(String(50), nullable=False, default="NORMAL")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    cow = relationship("Cow", back_populates="temperature_records")

    @property
    def tag_id(self) -> str:
        return self.cow.tag_id if self.cow else ""


class TemperatureBaseline(Base):
    """
    Stores the cow's 24-hour diurnal body temperature profile (0-23 hours).
    Each hour maintains a 7-day rolling mean and standard deviation.
    """
    __tablename__ = "temperature_baselines"

    id = Column(Integer, primary_key=True, index=True)
    cow_id = Column(Integer, ForeignKey("cows.id", ondelete="CASCADE"), nullable=False, index=True)
    hour_of_day = Column(Integer, nullable=False)  # 0 to 23
    mean_temperature = Column(Float, nullable=False)  # Baseline temperature in °C
    std_temperature = Column(Float, nullable=False, default=0.35)
    sample_count = Column(Integer, nullable=False, default=0)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    cow = relationship("Cow", back_populates="temperature_baselines")
