from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CowTelemetrySnapshot(BaseModel):
    """
    Consolidated multi-sensor parameters of a cow at a given moment.
    Can be loaded directly from database or provided via API payload.
    """
    cow_id: int = Field(..., description="Unique cow identifier")
    cow_tag: Optional[str] = Field("COW-001", description="Collar ear tag or identifier")
    breed: Optional[str] = Field("Holstein-Friesian", description="Cow breed")
    lactation_stage: Optional[str] = Field("Mid-Lactation", description="Lactation stage or parity")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Measurement timestamp")

    # Modality 1: Activity & Time-Budget
    current_activity: Optional[str] = Field("standing", description="Current activity: standing, lying, eating, walking")
    activity_confidence: Optional[float] = Field(0.95, description="Confidence of activity prediction (0-1)")
    daily_grazing_hours: Optional[float] = Field(None, description="Total grazing hours in past 24h")
    daily_lying_hours: Optional[float] = Field(None, description="Total lying hours in past 24h")
    daily_walking_hours: Optional[float] = Field(None, description="Total walking hours in past 24h")
    active_activity_alerts: Optional[List[str]] = Field(default_factory=list, description="Active rule alerts: FEEDING_DEFICIT, ESTRUS_SUSPECTED, LAMENESS_SUSPECTED")

    # Modality 2: Temperature & CUSUM
    skin_temperature: Optional[float] = Field(None, description="Raw skin temperature in °C")
    ambient_temperature: Optional[float] = Field(22.0, description="Ambient air temperature in °C")
    corrected_temperature: Optional[float] = Field(None, description="Ambient-decoupled body temperature in °C")
    temperature_status: Optional[str] = Field("NORMAL", description="Status: NORMAL, WARNING_FEVER, CRITICAL_FEVER, WARNING_HYPOTHERMIA, CRITICAL_HYPOTHERMIA")
    cusum_fever_score: Optional[float] = Field(0.0, description="CUSUM S+ cumulative fever score")
    cusum_hypo_score: Optional[float] = Field(0.0, description="CUSUM S- cumulative hypothermia score")

    # Modality 3: Heart Rate / Pulse
    heart_rate_bpm: Optional[float] = Field(None, description="Pulse rate in BPM")
    baseline_bpm: Optional[float] = Field(65.0, description="7-day personal resting baseline BPM")
    heart_rate_delta_pct: Optional[float] = Field(0.0, description="Percentage deviation from resting baseline")
    heart_rate_status: Optional[str] = Field("NORMAL", description="Status: NORMAL, HIGH_HEART_RATE, LOW_HEART_RATE")

    # Modality 4: GPS & Geofencing
    gps_lat: Optional[float] = Field(None, description="Current latitude")
    gps_lon: Optional[float] = Field(None, description="Current longitude")
    gps_behavior: Optional[str] = Field(None, description="GMM trajectory classification: Resting, Grazing, Walking")
    is_outside_geofence: Optional[bool] = Field(False, description="Whether currently outside pasture boundary")
    geofence_breach: Optional[bool] = Field(False, description="Debounced geofence breach alert flag")


class SimpleDiagnosticCard(BaseModel):
    """
    Standardized, clean, and farmer-friendly clinical diagnostic card.
    """
    cow_id: int
    cow_tag: Optional[str] = "COW-001"
    timestamp: str = Field(..., description="ISO-8601 evaluation timestamp")
    
    # Triage status
    triage_level: str = Field(..., description="NORMAL | MONITOR | ATTENTION | EMERGENCY")
    headline: str = Field(..., description="Concise 1-line condition verdict")
    farmer_message: str = Field(..., description="2-3 simple, plain-language sentences telling the farmer what this means")
    
    # Concise evidence and next steps
    key_indicators: List[str] = Field(..., description="Bullet list of 2-4 critical sensor observations")
    action_steps: List[str] = Field(..., description="Bullet list of 2-3 immediate practical actions for the farmer")
