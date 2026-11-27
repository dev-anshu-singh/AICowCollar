from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional, List
from sqlalchemy.orm import Session

from ..models.cow import Cow
from ..models.heart_rate import HeartRateRecord, HeartRateAlert

class HeartRateService:
    """
    Simplified Heart Rate Telemetry & Anomaly Service.
    
    1. Computes cow's personal baseline BPM (7-day rolling average) or defaults to 65.0 BPM.
    2. Compares incoming reading against baseline:
       - High Heart Rate: BPM >= 85 or Delta >= +30% (Pain / Fever / Stress)
       - Low Heart Rate: BPM <= 45 or Delta <= -25% (Milk Fever / Collapse / Sensor loose)
    3. Persists record and deduplicates alerts.
    """

    DEFAULT_BASELINE_BPM: float = 65.0

    # Rule 1 Thresholds (High Heart Rate / Tachycardia)
    HIGH_BPM_THRESHOLD: float = 85.0
    HIGH_DELTA_PCT_THRESHOLD: float = 30.0
    CRITICAL_HIGH_BPM: float = 100.0
    CRITICAL_HIGH_DELTA_PCT: float = 50.0

    # Rule 2 Thresholds (Low Heart Rate / Bradycardia)
    LOW_BPM_THRESHOLD: float = 45.0
    LOW_DELTA_PCT_THRESHOLD: float = -25.0
    CRITICAL_LOW_BPM: float = 38.0

    @classmethod
    def get_baseline_bpm(cls, cow_id: int, db: Session, days: int = 7) -> Tuple[float, int, bool]:
        """
        Calculates 7-day personal average heart rate from normal records.
        Returns (baseline_bpm, sample_count, is_custom).
        """
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
        records = db.query(HeartRateRecord).filter(
            HeartRateRecord.cow_id == cow_id,
            HeartRateRecord.status == "NORMAL",
            HeartRateRecord.timestamp >= cutoff
        ).all()

        if len(records) >= 3:
            avg_bpm = round(sum(r.heart_rate for r in records) / len(records), 1)
            return avg_bpm, len(records), True

        return cls.DEFAULT_BASELINE_BPM, len(records), False

    @classmethod
    def process_reading(
        cls,
        cow: Cow,
        heart_rate: float,
        timestamp: Optional[datetime] = None,
        db: Session = None
    ) -> Tuple[HeartRateRecord, Optional[HeartRateAlert]]:
        """
        Processes a single heart rate reading, checks threshold rules, and logs any alert.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        ts_naive = timestamp.replace(tzinfo=None) if timestamp.tzinfo is not None else timestamp

        # 1. Fetch personal baseline
        baseline_bpm, _, _ = cls.get_baseline_bpm(cow.id, db)

        # 2. Compute deltas
        delta_bpm = round(heart_rate - baseline_bpm, 1)
        delta_pct = round(((heart_rate - baseline_bpm) / baseline_bpm) * 100.0, 1)

        # 3. Evaluate 2 Simple Threshold Rules
        status = "NORMAL"
        severity = "INFO"
        clinical_notes = None
        alert = None

        if heart_rate >= cls.HIGH_BPM_THRESHOLD or delta_pct >= cls.HIGH_DELTA_PCT_THRESHOLD:
            status = "HIGH_HEART_RATE"
            is_critical = (heart_rate >= cls.CRITICAL_HIGH_BPM or delta_pct >= cls.CRITICAL_HIGH_DELTA_PCT)
            severity = "CRITICAL" if is_critical else "WARNING"
            clinical_notes = (
                f"Elevated heart rate detected: {heart_rate:.0f} BPM "
                f"({delta_pct:+.1f}% above baseline of {baseline_bpm:.0f} BPM). "
                f"Suspected pain, acute stress, fever, or physical distress."
            )
        elif heart_rate <= cls.LOW_BPM_THRESHOLD or delta_pct <= cls.LOW_DELTA_PCT_THRESHOLD:
            status = "LOW_HEART_RATE"
            is_critical = (heart_rate <= cls.CRITICAL_LOW_BPM)
            severity = "CRITICAL" if is_critical else "WARNING"
            clinical_notes = (
                f"Abnormally low heart rate detected: {heart_rate:.0f} BPM "
                f"({delta_pct:+.1f}% below baseline of {baseline_bpm:.0f} BPM). "
                f"Suspected lethargy, milk fever (hypocalcemia), or sensor detachment."
            )

        # Create Record
        record = HeartRateRecord(
            cow_id=cow.id,
            timestamp=ts_naive,
            heart_rate=round(heart_rate, 1),
            baseline_bpm=baseline_bpm,
            delta_bpm=delta_bpm,
            delta_pct=delta_pct,
            status=status
        )
        db.add(record)
        db.flush()

        # Deduplicate and log alert if triggered
        if status != "NORMAL":
            recent_alert = db.query(HeartRateAlert).filter(
                HeartRateAlert.cow_id == cow.id,
                HeartRateAlert.alert_type == status,
                HeartRateAlert.timestamp >= ts_naive - timedelta(hours=4)
            ).first()

            if not recent_alert:
                alert = HeartRateAlert(
                    cow_id=cow.id,
                    timestamp=ts_naive,
                    alert_type=status,
                    severity=severity,
                    current_bpm=round(heart_rate, 1),
                    baseline_bpm=baseline_bpm,
                    delta_pct=delta_pct,
                    clinical_notes=clinical_notes,
                    acknowledged=False
                )
                db.add(alert)
                db.flush()

        db.commit()
        db.refresh(record)
        if alert:
            db.refresh(alert)

        return record, alert

heart_rate_service = HeartRateService()
