from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List

class HeartRateTelemetryCreate(BaseModel):
    tag_id: str = Field(..., description="Unique cow tag identifier, e.g., COW_01")
    timestamp: Optional[datetime] = Field(default=None, description="Timestamp of measurement. Defaults to UTC now.")
    heart_rate: float = Field(..., ge=20.0, le=220.0, description="Measured heart rate in Beats Per Minute (BPM)")

class HeartRateTelemetryReading(BaseModel):
    timestamp: datetime
    heart_rate: float = Field(..., ge=20.0, le=220.0)

class HeartRateTelemetryBatch(BaseModel):
    tag_id: str = Field(..., description="Unique cow tag identifier")
    readings: List[HeartRateTelemetryReading] = Field(..., description="Chronological list of heart rate readings")

class HeartRateRecordResponse(BaseModel):
    id: int
    tag_id: str
    timestamp: datetime
    heart_rate: float
    baseline_bpm: float
    delta_bpm: float
    delta_pct: float
    status: str
    alert_triggered: bool = False
    clinical_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class HeartRateBaselineResponse(BaseModel):
    tag_id: str
    baseline_bpm: float
    sample_count: int
    is_custom_baseline: bool

class HeartRateAlertResponse(BaseModel):
    id: int
    tag_id: str
    timestamp: datetime
    alert_type: str
    severity: str
    current_bpm: float
    baseline_bpm: float
    delta_pct: float
    clinical_notes: str
    acknowledged: bool

    model_config = ConfigDict(from_attributes=True)
