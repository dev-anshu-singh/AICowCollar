from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Cow, HeartRateRecord, HeartRateAlert
from ..schemas.heart_rate import (
    HeartRateTelemetryCreate,
    HeartRateTelemetryBatch,
    HeartRateRecordResponse,
    HeartRateBaselineResponse,
    HeartRateAlertResponse,
)
from ..services import heart_rate_service

router = APIRouter(prefix="/heart-rate", tags=["Heart Rate Service"])

@router.post("/telemetry", response_model=HeartRateRecordResponse, status_code=status.HTTP_201_CREATED)
def ingest_heart_rate_telemetry(payload: HeartRateTelemetryCreate, db: Session = Depends(get_db)):
    """
    Ingests a single heart rate reading (BPM):
    1. Looks up or registers cow.
    2. Fetches 7-day personal baseline (or default 65.0 BPM).
    3. Evaluates simple high/low threshold rules.
    4. Automatically flags and persists alerts.
    """
    cow = db.query(Cow).filter(Cow.tag_id == payload.tag_id).first()
    if not cow:
        cow = Cow(tag_id=payload.tag_id, name=f"Cow {payload.tag_id}")
        db.add(cow)
        db.commit()
        db.refresh(cow)

    record, alert = heart_rate_service.process_reading(
        cow=cow,
        heart_rate=payload.heart_rate,
        timestamp=payload.timestamp,
        db=db
    )

    return HeartRateRecordResponse(
        id=record.id,
        tag_id=cow.tag_id,
        timestamp=record.timestamp,
        heart_rate=record.heart_rate,
        baseline_bpm=record.baseline_bpm,
        delta_bpm=record.delta_bpm,
        delta_pct=record.delta_pct,
        status=record.status,
        alert_triggered=alert is not None,
        clinical_notes=alert.clinical_notes if alert else None
    )


@router.post("/telemetry/batch", status_code=status.HTTP_201_CREATED)
def ingest_heart_rate_batch(payload: HeartRateTelemetryBatch, db: Session = Depends(get_db)):
    """
    Ingests a chronological stream/burst of heart rate telemetry readings.
    """
    cow = db.query(Cow).filter(Cow.tag_id == payload.tag_id).first()
    if not cow:
        cow = Cow(tag_id=payload.tag_id, name=f"Cow {payload.tag_id}")
        db.add(cow)
        db.commit()
        db.refresh(cow)

    sorted_readings = sorted(payload.readings, key=lambda r: r.timestamp)
    alerts_count = 0
    latest_record = None

    for item in sorted_readings:
        record, alert = heart_rate_service.process_reading(
            cow=cow,
            heart_rate=item.heart_rate,
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
        "latest_heart_rate": latest_record.heart_rate if latest_record else None,
        "latest_status": latest_record.status if latest_record else "NORMAL",
        "latest_delta_pct": latest_record.delta_pct if latest_record else 0.0
    }


@router.get("/cow/{tag_id}/records", response_model=List[HeartRateRecordResponse])
def get_heart_rate_records(tag_id: str, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieves recent heart rate records for a cow.
    """
    cow = db.query(Cow).filter(Cow.tag_id == tag_id).first()
    if not cow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cow '{tag_id}' not found.")

    records = db.query(HeartRateRecord).filter(
        HeartRateRecord.cow_id == cow.id
    ).order_by(HeartRateRecord.timestamp.desc()).limit(limit).all()

    return [
        HeartRateRecordResponse(
            id=r.id,
            tag_id=cow.tag_id,
            timestamp=r.timestamp,
            heart_rate=r.heart_rate,
            baseline_bpm=r.baseline_bpm,
            delta_bpm=r.delta_bpm,
            delta_pct=r.delta_pct,
            status=r.status,
            alert_triggered=r.status != "NORMAL",
            clinical_notes=None
        )
        for r in records
    ]


@router.get("/cow/{tag_id}/baseline", response_model=HeartRateBaselineResponse)
def get_heart_rate_baseline(tag_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the cow's current baseline heart rate.
    """
    cow = db.query(Cow).filter(Cow.tag_id == tag_id).first()
    if not cow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cow '{tag_id}' not found.")

    baseline_bpm, sample_count, is_custom = heart_rate_service.get_baseline_bpm(cow.id, db)
    return HeartRateBaselineResponse(
        tag_id=cow.tag_id,
        baseline_bpm=baseline_bpm,
        sample_count=sample_count,
        is_custom_baseline=is_custom
    )


@router.get("/cow/{tag_id}/alerts", response_model=List[HeartRateAlertResponse])
def get_heart_rate_alerts(tag_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """
    Lists historical heart rate alerts (High / Low Heart Rate) for a cow.
    """
    cow = db.query(Cow).filter(Cow.tag_id == tag_id).first()
    if not cow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cow '{tag_id}' not found.")

    alerts = db.query(HeartRateAlert).filter(
        HeartRateAlert.cow_id == cow.id
    ).order_by(HeartRateAlert.timestamp.desc()).limit(limit).all()

    return alerts


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_heart_rate_alert(alert_id: int, db: Session = Depends(get_db)):
    """
    Marks a heart rate alert as acknowledged.
    """
    alert = db.query(HeartRateAlert).filter(HeartRateAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert with ID {alert_id} not found.")

    alert.acknowledged = True
    db.commit()
    return {"status": "success", "alert_id": alert_id, "acknowledged": True}
