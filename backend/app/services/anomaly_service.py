from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, List, Optional
from ..models import ActivityRecord, DailyActivitySummary, ActivityAlert, Cow

class ActivityAnomalyService:
    @staticmethod
    def compute_daily_time_budget(cow_id: int, target_date: date, db: Session) -> DailyActivitySummary:
        """
        Aggregates all 1-minute ActivityRecords for a cow on a given date into daily hours
        and posture transition counts.
        """
        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = datetime.combine(target_date, datetime.max.time())

        # Query all records for this cow and date, ordered chronologically
        records = db.query(ActivityRecord).filter(
            ActivityRecord.cow_id == cow_id,
            ActivityRecord.timestamp >= start_dt,
            ActivityRecord.timestamp <= end_dt
        ).order_by(ActivityRecord.timestamp.asc()).all()

        if not records:
            # Check if summary already exists or return zeroed summary
            summary = db.query(DailyActivitySummary).filter(
                DailyActivitySummary.cow_id == cow_id,
                DailyActivitySummary.date == target_date
            ).first()
            if not summary:
                summary = DailyActivitySummary(
                    cow_id=cow_id,
                    date=target_date,
                    lying_hours=0.0,
                    standing_hours=0.0,
                    eating_hours=0.0,
                    walking_hours=0.0,
                    posture_transitions=0,
                    total_minutes_recorded=0
                )
                db.add(summary)
                db.commit()
                db.refresh(summary)
            return summary

        # Count minutes per behavior
        counts = {"lying": 0, "standing": 0, "eating": 0, "walking": 0}
        transitions = 0
        prev_behavior = None

        for rec in records:
            b = rec.predicted_behavior.lower()
            if b in counts:
                counts[b] += 1
            if prev_behavior is not None and b != prev_behavior:
                transitions += 1
            prev_behavior = b

        total_mins = len(records)
        
        # Check if daily summary already exists
        summary = db.query(DailyActivitySummary).filter(
            DailyActivitySummary.cow_id == cow_id,
            DailyActivitySummary.date == target_date
        ).first()

        if not summary:
            summary = DailyActivitySummary(cow_id=cow_id, date=target_date)
            db.add(summary)

        summary.lying_hours = round(counts["lying"] / 60.0, 2)
        summary.standing_hours = round(counts["standing"] / 60.0, 2)
        summary.eating_hours = round(counts["eating"] / 60.0, 2)
        summary.walking_hours = round(counts["walking"] / 60.0, 2)
        summary.posture_transitions = transitions
        summary.total_minutes_recorded = total_mins

        db.commit()
        db.refresh(summary)
        return summary

    @staticmethod
    def compute_7day_baseline(cow_id: int, current_date: date, db: Session) -> Dict[str, float]:
        """
        Computes the rolling 7-day average baseline for a cow prior to current_date.
        Falls back to clinical bovine standard averages if insufficient history.
        """
        start_date = current_date - timedelta(days=7)
        past_summaries = db.query(DailyActivitySummary).filter(
            DailyActivitySummary.cow_id == cow_id,
            DailyActivitySummary.date >= start_date,
            DailyActivitySummary.date < current_date
        ).all()

        # Clinical default reference values for Holstein-Friesian cattle
        if not past_summaries or len(past_summaries) < 2:
            return {
                "eating_hours": 4.50,
                "walking_hours": 0.80,
                "lying_hours": 11.50,
                "standing_hours": 7.20,
                "posture_transitions": 10,
                "days_in_baseline": len(past_summaries),
                "is_default": True
            }

        n = len(past_summaries)
        avg_eat = sum(s.eating_hours for s in past_summaries) / n
        avg_walk = sum(s.walking_hours for s in past_summaries) / n
        avg_lie = sum(s.lying_hours for s in past_summaries) / n
        avg_stand = sum(s.standing_hours for s in past_summaries) / n
        avg_trans = sum(s.posture_transitions for s in past_summaries) / n

        return {
            "eating_hours": round(avg_eat, 2),
            "walking_hours": round(avg_walk, 2),
            "lying_hours": round(avg_lie, 2),
            "standing_hours": round(avg_stand, 2),
            "posture_transitions": int(round(avg_trans)),
            "days_in_baseline": n,
            "is_default": False
        }

    @classmethod
    def evaluate_activity_anomalies(cls, cow_id: int, target_date: date, db: Session, recompute_summary: bool = True) -> dict:
        """
        Executes the simplified 3-step veterinary anomaly detection rule engine:
        1. Compares today's time-budget against 7-day baseline
        2. Computes percentage shifts (Δ% Eating, Δ% Walking, Δ% Lying)
        3. Evaluates 3 distinct clinical flags (Feeding Deficit, Estrus, Lameness)
        """
        cow = db.query(Cow).filter(Cow.id == cow_id).first()
        if not cow:
            raise ValueError(f"Cow with id {cow_id} not found.")

        # Step 1: Ensure daily time-budget is calculated
        if recompute_summary:
            summary = cls.compute_daily_time_budget(cow_id, target_date, db)
        else:
            summary = db.query(DailyActivitySummary).filter(
                DailyActivitySummary.cow_id == cow_id,
                DailyActivitySummary.date == target_date
            ).first()
            if not summary:
                summary = cls.compute_daily_time_budget(cow_id, target_date, db)

        # Step 2: Compute 7-day rolling personal baseline
        baseline = cls.compute_7day_baseline(cow_id, target_date, db)

        # Calculate percentage deviations: Δ% = (Today - Baseline) / Baseline * 100
        def calc_delta(current: float, base: float) -> float:
            if base <= 0:
                return 0.0
            return round(((current - base) / base) * 100.0, 1)

        delta_eat = calc_delta(summary.eating_hours, baseline["eating_hours"])
        delta_walk = calc_delta(summary.walking_hours, baseline["walking_hours"])
        delta_lie = calc_delta(summary.lying_hours, baseline["lying_hours"])

        # Step 3: Evaluate 3 Clinical Rules
        active_alerts = []
        status = "NORMAL_HEALTHY"
        severity = "INFO"
        message = f"Cow {cow.tag_id} activity is within normal baseline parameters."

        # Rule 1: Feeding Deficit (Suspected Sickness / Mastitis / Acidosis)
        if delta_eat <= -30.0:
            status = "FLAG_FEEDING_DEFICIT"
            severity = "CRITICAL"
            message = (
                f"Feeding intake dropped by {abs(delta_eat):.1f}% compared to 7-day baseline "
                f"({summary.eating_hours:.1f}h vs normal {baseline['eating_hours']:.1f}h). Suspected acute sickness or digestive distress."
            )
            active_alerts.append(status)

        # Rule 2: Hyperactivity / Estrus (Cow in Standing Heat)
        elif delta_walk >= 100.0 and delta_lie <= -30.0:
            status = "FLAG_ESTRUS_RESTLESSNESS"
            severity = "WARNING"
            message = (
                f"Walking surged by +{delta_walk:.1f}% with a {abs(delta_lie):.1f}% drop in resting/lying time. "
                f"Cow is exhibiting standing heat restlessness. Insemination window active."
            )
            active_alerts.append(status)

        # Rule 3: Excessive Inactivity (Suspected Lameness / Hoof injury)
        elif summary.lying_hours >= 14.0 and delta_walk <= -30.0:
            status = "FLAG_EXCESSIVE_LYING_LAMENESS"
            severity = "WARNING"
            message = (
                f"Excessive lying time ({summary.lying_hours:.1f}h/day) coupled with {abs(delta_walk):.1f}% drop in walking. "
                f"Reluctance to stand up indicates potential hoof lesion or joint pain."
            )
            active_alerts.append(status)

        # If an anomaly was detected, persist it in the activity_alerts table
        if active_alerts:
            # Check if this alert was already saved today to avoid duplicates
            today_start = datetime.combine(target_date, datetime.min.time())
            today_end = datetime.combine(target_date, datetime.max.time())
            
            existing = db.query(ActivityAlert).filter(
                ActivityAlert.cow_id == cow_id,
                ActivityAlert.alert_type == status,
                ActivityAlert.timestamp >= today_start,
                ActivityAlert.timestamp <= today_end
            ).first()

            if not existing:
                alert_record = ActivityAlert(
                    cow_id=cow_id,
                    timestamp=datetime.now(timezone.utc),
                    alert_type=status,
                    severity=severity,
                    eating_change_pct=delta_eat,
                    walking_change_pct=delta_walk,
                    lying_change_pct=delta_lie,
                    baseline_eating_hours=baseline["eating_hours"],
                    current_eating_hours=summary.eating_hours,
                    baseline_walking_hours=baseline["walking_hours"],
                    current_walking_hours=summary.walking_hours,
                    baseline_lying_hours=baseline["lying_hours"],
                    current_lying_hours=summary.lying_hours,
                    message=message
                )
                db.add(alert_record)
                db.commit()

        return {
            "cow_id": cow_id,
            "tag_id": cow.tag_id,
            "evaluation_date": str(target_date),
            "evaluation_window": "24-Hour Daily Time-Budget",
            "has_anomaly": len(active_alerts) > 0,
            "status": status,
            "severity": severity,
            "current_time_budget": {
                "eating_hours": summary.eating_hours,
                "walking_hours": summary.walking_hours,
                "lying_hours": summary.lying_hours,
                "standing_hours": summary.standing_hours,
                "posture_transitions": summary.posture_transitions,
                "total_minutes": summary.total_minutes_recorded
            },
            "baseline_7day": baseline,
            "deviations_pct": {
                "eating_delta_pct": delta_eat,
                "walking_delta_pct": delta_walk,
                "lying_delta_pct": delta_lie
            },
            "active_alerts": active_alerts,
            "clinical_notes": message
        }

anomaly_service = ActivityAnomalyService()
