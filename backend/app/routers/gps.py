from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Cow, GPSRecord, GPSAlert
from ..schemas.gps import (
    GPSTelemetryPayload,
    GPSRecordResponse,
    GPSAlertResponse,
    FarmPolygonResponse,
)
from ..services import gps_service

router = APIRouter(prefix="/gps", tags=["GPS & Geofencing Service"])

@router.post("/telemetry", response_model=GPSRecordResponse, status_code=status.HTTP_201_CREATED)
def ingest_gps_telemetry(payload: GPSTelemetryPayload, db: Session = Depends(get_db)):
    """
    Ingests GPS telemetry (single fix or sliding window of fixes):
    1. Looks up or auto-registers cow tag.
    2. Runs Ray-Casting Point-in-Polygon boundary check.
    3. Evaluates 2-strike debounce filter (prevents false alarms from jitter).
    4. Predicts GMM movement behavior (Resting, Grazing, Walking).
    5. Persists trajectory record and creates CRITICAL alert on confirmed breach.
    """
    cow = db.query(Cow).filter(Cow.tag_id == payload.tag_id).first()
    if not cow:
        cow = Cow(tag_id=payload.tag_id, name=f"Cow {payload.tag_id}")
        db.add(cow)
        db.commit()
        db.refresh(cow)

    fixes_dict = [f.model_dump() for f in payload.fixes] if payload.fixes else None
    single_fix_dict = payload.single_fix.model_dump() if payload.single_fix else None

    if not fixes_dict and not single_fix_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload must include either 'fixes' list or 'single_fix'."
        )

    record, alert = gps_service.process_telemetry(
        cow=cow,
        fixes=fixes_dict,
        single_fix=single_fix_dict,
        db=db
    )

    return GPSRecordResponse(
        id=record.id,
        tag_id=cow.tag_id,
        timestamp=record.timestamp,
        lat=record.lat,
        lon=record.lon,
        ttf_ms=record.ttf_ms,
        speed_mps=record.speed_mps,
        gps_behavior=record.gps_behavior,
        is_outside=record.is_outside,
        geofence_breach=record.geofence_breach,
        alert_message=record.alert_message or "OK"
    )


@router.get("/cow/{tag_id}/records", response_model=List[GPSRecordResponse])
def get_gps_records(tag_id: str, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieves recent GPS location history for map visualization and breadcrumb trails.
    """
    cow = db.query(Cow).filter(Cow.tag_id == tag_id).first()
    if not cow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cow '{tag_id}' not found.")

    records = db.query(GPSRecord).filter(
        GPSRecord.cow_id == cow.id
    ).order_by(GPSRecord.timestamp.desc()).limit(limit).all()

    return [
        GPSRecordResponse(
            id=r.id,
            tag_id=cow.tag_id,
            timestamp=r.timestamp,
            lat=r.lat,
            lon=r.lon,
            ttf_ms=r.ttf_ms,
            speed_mps=r.speed_mps,
            gps_behavior=r.gps_behavior,
            is_outside=r.is_outside,
            geofence_breach=r.geofence_breach,
            alert_message=r.alert_message or "OK"
        )
        for r in records
    ]


@router.get("/cow/{tag_id}/alerts", response_model=List[GPSAlertResponse])
def get_gps_alerts(tag_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """
    Retrieves historical geofence breach alerts for a cow.
    """
    cow = db.query(Cow).filter(Cow.tag_id == tag_id).first()
    if not cow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cow '{tag_id}' not found.")

    alerts = db.query(GPSAlert).filter(
        GPSAlert.cow_id == cow.id
    ).order_by(GPSAlert.timestamp.desc()).limit(limit).all()

    return alerts


@router.get("/farm-polygon", response_model=FarmPolygonResponse)
def get_farm_polygon():
    """
    Returns the farm boundary polygon coordinates for UI map overlays.
    """
    poly = gps_service.get_farm_polygon()
    return FarmPolygonResponse(
        polygon=poly,
        total_vertices=len(poly),
        description="Active pasture perimeter polygon for Ray-Casting Geofence checking."
    )


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_gps_alert(alert_id: int, db: Session = Depends(get_db)):
    """
    Marks a geofence breach alert as acknowledged.
    """
    alert = db.query(GPSAlert).filter(GPSAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert with ID {alert_id} not found.")

    alert.acknowledged = True
    db.commit()
    return {"status": "success", "alert_id": alert_id, "acknowledged": True}
