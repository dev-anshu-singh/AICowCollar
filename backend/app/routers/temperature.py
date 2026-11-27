from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import Cow, TemperatureRecord, TemperatureBaseline, TemperatureAlert
from ..schemas.temperature import (
    TemperatureTelemetryCreate,
    TemperatureTelemetryBatch,
    TemperatureRecordResponse,
    TemperatureBaselineResponse,
    HourlyBaseline,
    TemperatureAlertResponse
)
from ..services import temperature_service

router = APIRouter(prefix="/temperature", tags=["Temperature & CUSUM Anomaly Service"])

@router.post("/telemetry", response_model=TemperatureRecordResponse, status_code=status.HTTP_201_CREATED)
def ingest_temperature_telemetry(payload: TemperatureTelemetryCreate, db: Session = Depends(get_db)):
    """
    Ingests a temperature reading from a collar sensor (e.g. neck skin sensor + ambient sensor):
    1. Removes ambient environmental interference (ambient decoupling).
    2. Detrends against the cow's 24h circadian rhythm baseline for the current hour.
    3. Runs tabular CUSUM (Cumulative Sum Control Chart) for early fever or hypothermia detection.
    4. Automatically flags and persists alerts when CUSUM exceeds decision thresholds.
    """
    cow = db.query(Cow).filter(Cow.tag_id == payload.tag_id).first()
    if not cow:
        # Auto-register cow if not present
        cow = Cow(tag_id=payload.tag_id, name=f"Cow {payload.tag_id}")
        db.add(cow)
        db.commit()
        db.refresh(cow)

    record, alert = temperature_service.process_reading(
        cow=cow,
        skin_temp=payload.skin_temperature,
        ambient_temp=payload.ambient_temperature,
        timestamp=payload.timestamp,
        db=db
    )

    response = TemperatureRecordResponse(
        id=record.id,
        tag_id=cow.tag_id,
        timestamp=record.timestamp,
        skin_temperature=record.skin_temperature,
        ambient_temperature=record.ambient_temperature,
        corrected_temperature=record.corrected_temperature,
        expected_baseline_temp=record.expected_baseline_temp,
        residual_delta=record.residual_delta,
        cusum_positive=record.cusum_positive,
        cusum_negative=record.cusum_negative,
        status=record.status,
        alert_triggered=alert is not None,
        clinical_notes=alert.clinical_notes if alert else None
    )
    return response


@router.post("/telemetry/batch", status_code=status.HTTP_201_CREATED)
def ingest_temperature_batch(payload: TemperatureTelemetryBatch, db: Session = Depends(get_db)):
    """
    Ingests a batch of chronological temperature readings (e.g. from an offline burst buffer or LoRa upload).
    """
    cow = db.query(Cow).filter(Cow.tag_id == payload.tag_id).first()
    if not cow:
        cow = Cow(tag_id=payload.tag_id, name=f"Cow {payload.tag_id}")
        db.add(cow)
        db.commit()
        db.refresh(cow)

    # Sort chronologically
    sorted_readings = sorted(payload.readings, key=lambda r: r.timestamp)
    alerts_count = 0
    latest_record = None

    for item in sorted_readings:
        record, alert = temperature_service.process_reading(
            cow=cow,
            skin_temp=item.skin_temperature,
            ambient_temp=item.ambient_temperature,
            timestamp=item.timestamp,
            db=db
        )
        if alert:
            alerts_count += 1
        latest_record = record

    return {
        "tag_id": cow.tag_id,
        "total_processed": len(sorted_readings),
        "alerts_triggered": alerts_count,
        "latest_status": latest_record.status if latest_record else "NORMAL",
        "latest_corrected_temp": latest_record.corrected_temperature if latest_record else None,
        "latest_cusum_positive": latest_record.cusum_positive if latest_record else 0.0,
        "latest_cusum_negative": latest_record.cusum_negative if latest_record else 0.0,
    }


@router.get("/cow/{tag_id}/records", response_model=List[TemperatureRecordResponse])
def get_temperature_records(tag_id: str, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieves recent temperature records with CUSUM metrics for a cow.
    """
    cow = db.query(Cow).filter(Cow.tag_id == tag_id).first()
    if not cow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cow '{tag_id}' not found.")

    records = db.query(TemperatureRecord).filter(
        TemperatureRecord.cow_id == cow.id
    ).order_by(TemperatureRecord.timestamp.desc()).limit(limit).all()

    return [
        TemperatureRecordResponse(
            id=r.id,
            tag_id=cow.tag_id,
            timestamp=r.timestamp,
            skin_temperature=r.skin_temperature,
            ambient_temperature=r.ambient_temperature,
            corrected_temperature=r.corrected_temperature,
            expected_baseline_temp=r.expected_baseline_temp,
            residual_delta=r.residual_delta,
            cusum_positive=r.cusum_positive,
            cusum_negative=r.cusum_negative,
            status=r.status,
            alert_triggered=r.status != "NORMAL",
            clinical_notes=None
        )
        for r in records
    ]


@router.get("/cow/{tag_id}/baseline", response_model=TemperatureBaselineResponse)
def get_temperature_baseline(tag_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the 24-hour diurnal body temperature profile for a cow.
    Shows the expected healthy mean temperature and standard deviation for each hour of day (0-23).
    """
    cow = db.query(Cow).filter(Cow.tag_id == tag_id).first()
    if not cow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cow '{tag_id}' not found.")

    baselines = db.query(TemperatureBaseline).filter(
        TemperatureBaseline.cow_id == cow.id
    ).order_by(TemperatureBaseline.hour_of_day.asc()).all()

    is_custom = len(baselines) == 24 and any(b.sample_count >= 3 for b in baselines)
    
    profile = []
    if is_custom:
        for b in baselines:
            profile.append(HourlyBaseline(
                hour_of_day=b.hour_of_day,
                mean_temperature=b.mean_temperature,
                std_temperature=b.std_temperature,
                sample_count=b.sample_count
            ))
    else:
        for h in range(24):
            m, s = temperature_service.get_default_circadian_temp(h)
            profile.append(HourlyBaseline(
                hour_of_day=h,
                mean_temperature=m,
                std_temperature=s,
                sample_count=0
            ))

    return TemperatureBaselineResponse(
        tag_id=cow.tag_id,
        is_custom_baseline=is_custom,
        diurnal_profile=profile
    )


@router.post("/cow/{tag_id}/recompute-baseline", response_model=TemperatureBaselineResponse)
def recompute_temperature_baseline(tag_id: str, days: int = Query(7, ge=1, le=30), db: Session = Depends(get_db)):
    """
    Aggregates historical non-fever temperature records from the past N days
    to update the cow's personalized 24-hour diurnal baseline.
    """
    cow = db.query(Cow).filter(Cow.tag_id == tag_id).first()
    if not cow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cow '{tag_id}' not found.")

    baselines = temperature_service.recompute_diurnal_baseline(cow.id, db, days=days)
    is_custom = any(b.sample_count >= 3 for b in baselines)

    return TemperatureBaselineResponse(
        tag_id=cow.tag_id,
        is_custom_baseline=is_custom,
        diurnal_profile=[
            HourlyBaseline(
                hour_of_day=b.hour_of_day,
                mean_temperature=b.mean_temperature,
                std_temperature=b.std_temperature,
                sample_count=b.sample_count
            )
            for b in sorted(baselines, key=lambda x: x.hour_of_day)
        ]
    )


@router.get("/cow/{tag_id}/alerts", response_model=List[TemperatureAlertResponse])
def get_temperature_alerts(tag_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """
    Lists historical temperature anomaly alerts (Suspected Fever, Hypothermia) for a cow.
    """
    cow = db.query(Cow).filter(Cow.tag_id == tag_id).first()
    if not cow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cow '{tag_id}' not found.")

    alerts = db.query(TemperatureAlert).filter(
        TemperatureAlert.cow_id == cow.id
    ).order_by(TemperatureAlert.timestamp.desc()).limit(limit).all()

    return alerts


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_temperature_alert(alert_id: int, db: Session = Depends(get_db)):
    """
    Marks a temperature alert as acknowledged by farm personnel or veterinarian.
    """
    alert = db.query(TemperatureAlert).filter(TemperatureAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert with ID {alert_id} not found.")

    alert.acknowledged = True
    db.commit()
    return {"status": "success", "alert_id": alert_id, "acknowledged": True}
