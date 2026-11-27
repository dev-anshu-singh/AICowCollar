from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Tuple

class GPSFix(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    timestamp: Optional[datetime] = Field(default=None, description="Timestamp of fix (defaults to UTC now)")
    ttf_ms: Optional[float] = Field(default=1000.0, description="Time to first fix in milliseconds")

class GPSTelemetryPayload(BaseModel):
    tag_id: str = Field(..., description="Unique cow tag identifier, e.g. COW_01")
    # Supports either a single live fix (backend fetches recent history) OR an explicit window/batch of fixes
    fixes: Optional[List[GPSFix]] = Field(default=None, description="Sliding window of fixes (recommended: 7 fixes)")
    single_fix: Optional[GPSFix] = Field(default=None, description="Single fix; service queries previous fixes from DB to construct window")

class GPSRecordResponse(BaseModel):
    id: int
    tag_id: str
    timestamp: datetime
    lat: float
    lon: float
    ttf_ms: Optional[float] = 1000.0
    speed_mps: Optional[float] = None
    gps_behavior: str
    is_outside: bool
    geofence_breach: bool
    alert_message: str

    model_config = ConfigDict(from_attributes=True)

class GPSAlertResponse(BaseModel):
    id: int
    tag_id: str
    timestamp: datetime
    alert_type: str
    severity: str
    lat: float
    lon: float
    message: str
    acknowledged: bool

    model_config = ConfigDict(from_attributes=True)

class FarmPolygonResponse(BaseModel):
    polygon: List[Tuple[float, float]]
    total_vertices: int
    description: str
