from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from ..database import get_db
from ..models import Cow, ActivityRecord, DailyActivitySummary, ActivityAlert
from ..schemas.activity import TelemetryPayload, ActivityRecordResponse, TimeBudgetResponse
from ..schemas.alert import AlertResponse, AnomalyEvaluationResponse
from ..services import classifier_service, anomaly_service

router = APIRouter(prefix="/activity", tags=["Activity & Anomaly Service"])

@router.post("/telemetry", response_model=ActivityRecordResponse, status_code=status.HTTP_201_CREATED)
def ingest_activity_telemetry(payload: TelemetryPayload, db: Session = Depends(get_db)):
    """
    Ingests a 1-minute telemetry packet from a collar tag:
    1. Looks up the cow by tag_id (registers if not present).
    2. Runs feature extraction if raw 10s buffer provided.
    3. Executes the 12-feature ExtraTrees classifier to predict behavior.
    4. Persists the classification record in the database.
    """
    cow = db.query(Cow).filter(Cow.tag_id == payload.tag_id).first()
    if not cow:
        # Auto-register new cow collar tag
        cow = Cow(tag_id=payload.tag_id, name=f"Cow {payload.tag_id}")
        db.add(cow)
        db.commit()
        db.refresh(cow)

    features = payload.features
    
    # Extract 12 physical features from raw buffer if provided
    if not features and payload.raw_buffer:
        if len(payload.raw_buffer) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="raw_buffer requires at least 2 readings (ideally 6 readings for 1-minute window)."
            )
        features = classifier_service.extract_12_features_from_buffer(payload.raw_buffer)

    if not features and not payload.predicted_behavior:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload must contain either 'features', 'raw_buffer', or 'predicted_behavior'."
        )

    # Classify behavior using trained 12-feature ML model
    if features:
        pred_behavior, confidence, probs = classifier_service.predict_behavior(features)
    else:
        pred_behavior = payload.predicted_behavior.lower()
        confidence = 1.0
        probs = {pred_behavior: 1.0}

    # Save to database
    record = ActivityRecord(
        cow_id=cow.id,
        timestamp=payload.timestamp,
        predicted_behavior=pred_behavior,
        confidence=confidence,
        probabilities=probs,
        features=features
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return record

@router.get("/cow/{tag_id}/records", response_model=List[ActivityRecordResponse])
def get_activity_records(tag_id: str, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieves recent minute-by-minute activity classification records for a cow.
    """
    cow = db.query(Cow).filter(Cow.tag_id == tag_id).first()
    if not cow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cow '{tag_id}' not found.")
    
    records = db.query(ActivityRecord).filter(
        ActivityRecord.cow_id == cow.id
    ).order_by(ActivityRecord.timestamp.desc()).limit(limit).all()
    
    return records

@router.get("/cow/{tag_id}/time-budget", response_model=TimeBudgetResponse)
def get_daily_time_budget(tag_id: str, target_date: Optional[date] = None, db: Session = Depends(get_db)):
    """
    Returns the aggregated daily time budget (hours lying, standing, eating, walking) for a date.
    """
    if target_date is None:
        target_date = date.today()

    cow = db.query(Cow).filter(Cow.tag_id == tag_id).first()
    if not cow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cow '{tag_id}' not found.")
    
    summary = anomaly_service.compute_daily_time_budget(cow.id, target_date, db)
    return summary

@router.post("/cow/{tag_id}/evaluate-anomalies", response_model=AnomalyEvaluationResponse)
def evaluate_anomalies(
    tag_id: str,
    target_date: Optional[date] = None,
    recompute_summary: bool = Query(True, description="Whether to recompute time budget from individual 1-minute records"),
    db: Session = Depends(get_db)
):
    """
    Executes the 3-step veterinary anomaly detection rule engine on the 24-hour time budget:
    1. Computes today's time-budget against 7-day personal baseline.
    2. Computes percentage shifts (Δ% Eating, Δ% Walking, Δ% Lying).
    3. Evaluates 3 distinct clinical flags (Feeding Deficit, Estrus, Lameness).
    """
    if target_date is None:
        target_date = date.today()

    cow = db.query(Cow).filter(Cow.tag_id == tag_id).first()
    if not cow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cow '{tag_id}' not found.")
    
    result = anomaly_service.evaluate_activity_anomalies(cow.id, target_date, db, recompute_summary=recompute_summary)
    return result

@router.get("/cow/{tag_id}/alerts", response_model=List[AlertResponse])
def get_cow_alerts(tag_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """
    Lists historical activity health alerts (e.g. Feeding Deficits, Estrus, Lameness) for a cow.
    """
    cow = db.query(Cow).filter(Cow.tag_id == tag_id).first()
    if not cow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cow '{tag_id}' not found.")
    
    alerts = db.query(ActivityAlert).filter(
        ActivityAlert.cow_id == cow.id
    ).order_by(ActivityAlert.timestamp.desc()).limit(limit).all()
    
    return alerts
