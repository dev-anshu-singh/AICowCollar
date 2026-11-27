from sqlalchemy import Column, Integer, Float, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..database import Base

class DailyActivitySummary(Base):
    __tablename__ = "daily_activity_summaries"

    id = Column(Integer, primary_key=True, index=True)
    cow_id = Column(Integer, ForeignKey("cows.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # Daily Time Budget (in Hours)
    lying_hours = Column(Float, default=0.0)
    standing_hours = Column(Float, default=0.0)
    eating_hours = Column(Float, default=0.0)
    walking_hours = Column(Float, default=0.0)
    
    # Counts
    posture_transitions = Column(Integer, default=0)
    total_minutes_recorded = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    cow = relationship("Cow", back_populates="daily_summaries")
