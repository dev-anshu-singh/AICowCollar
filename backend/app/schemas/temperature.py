from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List

class TemperatureTelemetryCreate(BaseModel):
    tag_id: str = Field(..., description="Unique cow tag identifier, e.g., COW_01")
    timestamp: Optional[datetime] = Field(default=None, description="Timestamp of measurement. Defaults to UTC now.")
    skin_temperature: float = Field(..., ge=25.0, le=46.0, description="Measured neck/skin temperature in °C")
    ambient_temperature: Optional[float] = Field(default=22.0, ge=-25.0, le=55.0, description="Ambient air temperature in °C")

class TemperatureTelemetryReading(BaseModel):
    timestamp: datetime
    skin_temperature: float = Field(..., ge=25.0, le=46.0)
    ambient_temperature: Optional[float] = Field(default=22.0, ge=-25.0, le=55.0)

class TemperatureTelemetryBatch(BaseModel):
    tag_id: str = Field(..., description="Unique cow tag identifier")
    readings: List[TemperatureTelemetryReading] = Field(..., description="Ordered list of historical or burst temperature readings")

class TemperatureRecordResponse(BaseModel):
    id: int
    tag_id: str
    timestamp: datetime
    skin_temperature: float
    ambient_temperature: float
    corrected_temperature: float
    expected_baseline_temp: float
    residual_delta: float
    cusum_positive: float
    cusum_negative: float
    status: str
    alert_triggered: bool = False
    clinical_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class HourlyBaseline(BaseModel):
    hour_of_day: int
    mean_temperature: float
    std_temperature: float
    sample_count: int

    model_config = ConfigDict(from_attributes=True)

class TemperatureBaselineResponse(BaseModel):
    tag_id: str
    is_custom_baseline: bool
    diurnal_profile: List[HourlyBaseline]

class TemperatureAlertResponse(BaseModel):
    id: int
    tag_id: str
    timestamp: datetime
    alert_type: str
    severity: str
    current_temp: float
    baseline_temp: float
    temp_delta: float
    cusum_score: float
    clinical_notes: str
    acknowledged: bool

    model_config = ConfigDict(from_attributes=True)
