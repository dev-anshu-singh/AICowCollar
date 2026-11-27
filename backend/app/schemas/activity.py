from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime, date

class TelemetryPayload(BaseModel):
    tag_id: str = Field(..., description="Collar Tag ID matching cow")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Option A: Send the 12 pre-calculated features directly
    features: Optional[Dict[str, float]] = Field(None, description="The 12 streamlined physical features")
    
    # Option B: Send raw 1-minute buffer of 6 readings (10s intervals: AccX, AccY, AccZ, GyroX, GyroY, GyroZ)
    raw_buffer: Optional[List[Dict[str, float]]] = Field(None, description="Raw 6x6 10s sensor readings for server-side feature extraction")
    
    # Option C: Direct behavior injection (if collar classified locally)
    predicted_behavior: Optional[str] = Field(None, description="'lying', 'standing', 'eating', 'walking'")

class ActivityRecordResponse(BaseModel):
    id: int
    cow_id: int
    timestamp: datetime
    predicted_behavior: str
    confidence: float
    probabilities: Optional[Dict[str, float]] = None

    class Config:
        from_attributes = True

class TimeBudgetResponse(BaseModel):
    cow_id: int
    date: date
    lying_hours: float
    standing_hours: float
    eating_hours: float
    walking_hours: float
    posture_transitions: int
    total_minutes_recorded: int

    class Config:
        from_attributes = True
