from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..database import Base

class Cow(Base):
    __tablename__ = "cows"

    id = Column(Integer, primary_key=True, index=True)
    tag_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    breed = Column(String(100), default="Holstein-Friesian")
    age_months = Column(Integer, nullable=True)
    lactation_stage = Column(String(50), default="Mid-Lactation")
    collar_battery_pct = Column(Float, default=100.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    activity_records = relationship("ActivityRecord", back_populates="cow", cascade="all, delete-orphan")
    daily_summaries = relationship("DailyActivitySummary", back_populates="cow", cascade="all, delete-orphan")
    alerts = relationship("ActivityAlert", back_populates="cow", cascade="all, delete-orphan")
    temperature_records = relationship("TemperatureRecord", back_populates="cow", cascade="all, delete-orphan")
    temperature_baselines = relationship("TemperatureBaseline", back_populates="cow", cascade="all, delete-orphan")
    temperature_alerts = relationship("TemperatureAlert", back_populates="cow", cascade="all, delete-orphan")
    heart_rate_records = relationship("HeartRateRecord", back_populates="cow", cascade="all, delete-orphan")
    heart_rate_alerts = relationship("HeartRateAlert", back_populates="cow", cascade="all, delete-orphan")
    gps_records = relationship("GPSRecord", back_populates="cow", cascade="all, delete-orphan")
    gps_alerts = relationship("GPSAlert", back_populates="cow", cascade="all, delete-orphan")
