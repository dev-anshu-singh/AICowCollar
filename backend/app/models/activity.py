from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ..database import Base

class ActivityRecord(Base):
    __tablename__ = "activity_records"

    id = Column(Integer, primary_key=True, index=True)
    cow_id = Column(Integer, ForeignKey("cows.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Classification Output
    predicted_behavior = Column(String(20), nullable=False)  # 'lying', 'standing', 'eating', 'walking'
    confidence = Column(Float, nullable=False)
    probabilities = Column(JSON, nullable=True)             # {'lying': 0.02, 'standing': 0.05, ...}
    
    # 12 Core Engineered Features (cached for auditing / model retraining)
    features = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    cow = relationship("Cow", back_populates="activity_records")
