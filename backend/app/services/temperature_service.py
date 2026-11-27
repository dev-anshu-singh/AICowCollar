import math
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.cow import Cow
from ..models.temperature import TemperatureRecord, TemperatureBaseline
from ..models.temperature_alert import TemperatureAlert

class TemperatureAnomalyService:
    """
    Veterinary CUSUM (Cumulative Sum Control Chart) temperature analytics service.
    
    Pipeline:
      1. Ambient Decoupling: Corrects skin temperature for ambient cooling/heating.
      2. Circadian Baseline Detrending: Subtracts diurnal expected temperature for that hour.
      3. Tabular CUSUM Accumulation:
         - S_t^+ = max(0, S_{t-1}^+ + (Delta_T - k))   -> Fever detection (Mastitis / BRD)
         - S_t^- = max(0, S_{t-1}^- + (-Delta_T - k))  -> Hypothermia (Milk Fever / Calving)
      4. Alert Triggering & Deduplication.
    """

    # Ambient decoupling constants (based on Bewley et al. & Lees et al.)
    BETA_AMBIENT: float = 0.12        # °C skin per °C ambient deviation
    T_REF_AMBIENT: float = 22.0       # Thermoneutral reference ambient temperature (°C)

    # CUSUM parameters (tuned for bovine thermal biology)
    K_SLACK: float = 0.30             # Slack allowance in °C (shifts <= 0.3°C do not accumulate)
    H_WARNING: float = 1.20           # Alarm threshold for WARNING severity
    H_CRITICAL: float = 2.00          # Alarm threshold for CRITICAL severity

    @classmethod
    def decouple_ambient_temperature(cls, skin_temp: float, ambient_temp: Optional[float] = None) -> float:
        """
        Removes ambient thermal effects from collar surface temperature.
        Formula: T_corrected = T_skin - beta * (T_ambient - T_ref)
        """
        if ambient_temp is None:
            return round(skin_temp, 2)
        
        corrected = skin_temp - cls.BETA_AMBIENT * (ambient_temp - cls.T_REF_AMBIENT)
        return round(corrected, 2)

    @classmethod
    def get_default_circadian_temp(cls, hour_of_day: int) -> Tuple[float, float]:
        """
        Default bovine circadian rhythm model if healthy baseline is not yet established.
        Peak is around 16:00-18:00 (~38.9°C), trough is around 04:00-06:00 (~38.1°C).
        Returns (mean_temp, std_temp).
        """
        # Peak at hour 16 (4 PM), trough at hour 4 (4 AM)
        # sin(2*pi * (h - 10)/24): at h=16, (16-10)/24 = 6/24 = 1/4 -> sin(pi/2) = +1
        # at h=4, (4-10)/24 = -6/24 = -1/4 -> sin(-pi/2) = -1
        radians = 2.0 * math.pi * (hour_of_day - 10.0) / 24.0
        expected_mean = 38.50 + 0.40 * math.sin(radians)
        expected_std = 0.35
        return round(expected_mean, 2), round(expected_std, 2)

    @classmethod
    def get_expected_baseline(cls, cow_id: int, hour_of_day: int, db: Session) -> Tuple[float, float, bool]:
        """
        Retrieves the cow's personalized 7-day hourly baseline if available;
        otherwise falls back to the default circadian curve.
        Returns (mean_temp, std_temp, is_personalized).
        """
        baseline = db.query(TemperatureBaseline).filter(
            TemperatureBaseline.cow_id == cow_id,
            TemperatureBaseline.hour_of_day == hour_of_day
        ).first()

        if baseline and baseline.sample_count >= 3:
            return round(baseline.mean_temperature, 2), round(baseline.std_temperature, 2), True
        
        default_mean, default_std = cls.get_default_circadian_temp(hour_of_day)
        return default_mean, default_std, False

    @classmethod
    def get_previous_cusum_state(cls, cow_id: int, current_ts: datetime, db: Session) -> Tuple[float, float]:
        """
        Retrieves the most recent CUSUM accumulator values for this cow.
        Resets to 0.0 if there is a telemetry gap > 6 hours.
        """
        ts_curr = current_ts.replace(tzinfo=None) if current_ts.tzinfo is not None else current_ts
        latest_record = db.query(TemperatureRecord).filter(
            TemperatureRecord.cow_id == cow_id,
            TemperatureRecord.timestamp < ts_curr
        ).order_by(TemperatureRecord.timestamp.desc()).first()

        if not latest_record:
            return 0.0, 0.0

        ts_last = latest_record.timestamp.replace(tzinfo=None) if latest_record.timestamp.tzinfo is not None else latest_record.timestamp
        gap = (ts_curr - ts_last).total_seconds()
        if gap > 6 * 3600:  # Gap greater than 6 hours resets accumulator
            return 0.0, 0.0

        return latest_record.cusum_positive, latest_record.cusum_negative

    @classmethod
    def process_reading(
        cls,
        cow: Cow,
        skin_temp: float,
        ambient_temp: Optional[float] = 22.0,
        timestamp: Optional[datetime] = None,
        db: Session = None
    ) -> Tuple[TemperatureRecord, Optional[TemperatureAlert]]:
        """
        End-to-end processing of a single temperature telemetry point.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        # Standardize to naive UTC for SQLite compatibility
        ts_naive = timestamp.replace(tzinfo=None) if timestamp.tzinfo is not None else timestamp

        # 1. Ambient Decoupling
        corrected_temp = cls.decouple_ambient_temperature(skin_temp, ambient_temp)

        # 2. Circadian Baseline Detrending
        hour = ts_naive.hour
        expected_mean, _, _ = cls.get_expected_baseline(cow.id, hour, db)
        delta_t = round(corrected_temp - expected_mean, 2)

        # 3. CUSUM Accumulation
        prev_s_pos, prev_s_neg = cls.get_previous_cusum_state(cow.id, ts_naive, db)
        
        # Upper CUSUM (Fever): S_t^+ = max(0, S_{t-1}^+ + (delta_t - k))
        s_pos = max(0.0, prev_s_pos + (delta_t - cls.K_SLACK))
        # Lower CUSUM (Hypothermia): S_t^- = max(0, S_{t-1}^- + (-delta_t - k))
        s_neg = max(0.0, prev_s_neg + (-delta_t - cls.K_SLACK))

        s_pos = round(s_pos, 2)
        s_neg = round(s_neg, 2)

        # 4. Anomaly Decision Logic
        status = "NORMAL"
        alert: Optional[TemperatureAlert] = None
        clinical_notes: Optional[str] = None
        severity: str = "INFO"

        if s_pos >= cls.H_WARNING:
            status = "SUSPECTED_FEVER"
            severity = "CRITICAL" if s_pos >= cls.H_CRITICAL else "WARNING"
            clinical_notes = (
                f"Persistent thermal elevation (CUSUM S+: {s_pos:.2f}, +{delta_t:.2f}°C above circadian baseline). "
                f"High likelihood of early mastitis, bovine respiratory disease (BRD), or systemic fever."
            )
        elif s_neg >= cls.H_WARNING:
            status = "SUSPECTED_HYPOTHERMIA"
            severity = "CRITICAL" if s_neg >= cls.H_CRITICAL else "WARNING"
            clinical_notes = (
                f"Persistent thermal depression (CUSUM S-: {s_neg:.2f}, {delta_t:.2f}°C below circadian baseline). "
                f"Early warning for milk fever (hypocalcemia), ketosis, or pre-calving drop."
            )

        # Create Record
        record = TemperatureRecord(
            cow_id=cow.id,
            timestamp=ts_naive,
            skin_temperature=round(skin_temp, 2),
            ambient_temperature=round(ambient_temp, 2) if ambient_temp is not None else 22.0,
            corrected_temperature=corrected_temp,
            expected_baseline_temp=expected_mean,
            residual_delta=delta_t,
            cusum_positive=s_pos,
            cusum_negative=s_neg,
            status=status
        )
        db.add(record)
        db.flush()

        # Deduplicate and persist alert if triggered
        if status != "NORMAL":
            recent_alert = db.query(TemperatureAlert).filter(
                TemperatureAlert.cow_id == cow.id,
                TemperatureAlert.alert_type == status,
                TemperatureAlert.timestamp >= ts_naive - timedelta(hours=4)
            ).first()

            if not recent_alert:
                alert = TemperatureAlert(
                    cow_id=cow.id,
                    timestamp=ts_naive,
                    alert_type=status,
                    severity=severity,
                    current_temp=corrected_temp,
                    baseline_temp=expected_mean,
                    temp_delta=delta_t,
                    cusum_score=s_pos if status == "SUSPECTED_FEVER" else s_neg,
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

    @classmethod
    def recompute_diurnal_baseline(cls, cow_id: int, db: Session, days: int = 7) -> List[TemperatureBaseline]:
        """
        Computes 24-hour diurnal baselines from healthy past days (status == NORMAL).
        """
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
        records = db.query(TemperatureRecord).filter(
            TemperatureRecord.cow_id == cow_id,
            TemperatureRecord.status == "NORMAL",
            TemperatureRecord.timestamp >= cutoff
        ).all()

        hourly_buckets: Dict[int, List[float]] = {h: [] for h in range(24)}
        for r in records:
            hourly_buckets[r.timestamp.hour].append(r.corrected_temperature)

        baselines = []
        for hour in range(24):
            temps = hourly_buckets[hour]
            if len(temps) >= 3:
                mean_t = float(sum(temps) / len(temps))
                variance = sum((x - mean_t) ** 2 for x in temps) / (len(temps) - 1) if len(temps) > 1 else 0.1
                std_t = max(0.15, float(math.sqrt(variance)))
                sample_count = len(temps)
            else:
                default_mean, default_std = cls.get_default_circadian_temp(hour)
                mean_t = default_mean
                std_t = default_std
                sample_count = len(temps)

            baseline = db.query(TemperatureBaseline).filter(
                TemperatureBaseline.cow_id == cow_id,
                TemperatureBaseline.hour_of_day == hour
            ).first()

            if not baseline:
                baseline = TemperatureBaseline(
                    cow_id=cow_id,
                    hour_of_day=hour,
                    mean_temperature=round(mean_t, 2),
                    std_temperature=round(std_t, 2),
                    sample_count=sample_count,
                    last_updated=datetime.now(timezone.utc)
                )
                db.add(baseline)
            else:
                baseline.mean_temperature = round(mean_t, 2)
                baseline.std_temperature = round(std_t, 2)
                baseline.sample_count = sample_count
                baseline.last_updated = datetime.now(timezone.utc)

            baselines.append(baseline)

        db.commit()
        return baselines

temperature_service = TemperatureAnomalyService()
