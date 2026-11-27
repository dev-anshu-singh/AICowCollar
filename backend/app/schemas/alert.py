from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AlertResponse(BaseModel):
    id: int
    cow_id: int
    timestamp: datetime
    alert_type: str
    severity: str
    eating_change_pct: Optional[float] = None
    walking_change_pct: Optional[float] = None
    lying_change_pct: Optional[float] = None
    message: str
    acknowledged: bool

    class Config:
        from_attributes = True

class AnomalyEvaluationResponse(BaseModel):
    cow_id: int
    tag_id: str
    evaluation_window: str
    has_anomaly: bool
    status: str
    current_time_budget: dict
    baseline_7day: dict
    deviations_pct: dict
    active_alerts: List[str]
    clinical_notes: str
