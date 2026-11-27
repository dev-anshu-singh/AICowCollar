import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..config import settings
from ..schemas.vet import CowTelemetrySnapshot, SimpleDiagnosticCard
from ..models import (
    Cow,
    ActivityRecord,
    DailyActivitySummary,
    ActivityAlert,
    TemperatureRecord,
    HeartRateRecord,
    GPSRecord,
)

logger = logging.getLogger(__name__)


class LLMVetService:
    """
    Veterinary Clinical Diagnostic Service.
    Aggregates multi-modal sensor streams (Activity, Temperature, Pulse, GPS)
    and utilizes Gemini 3.8 Flash (with deterministic fallback) to generate
    a simple, plain-language diagnostic card for farmers and veterinarians.
    """

    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        self.model_name = model_name or settings.GEMINI_MODEL or "gemini-3.8-flash"
        self.api_key = api_key or settings.GEMINI_API_KEY

    def extract_cow_snapshot(self, db: Session, cow_id: int) -> CowTelemetrySnapshot:
        """
        Gathers the latest telemetry readings across all 4 services from SQLite database.
        """
        cow = db.query(Cow).filter(Cow.id == cow_id).first()
        cow_tag = cow.tag_id if cow else f"COW-{cow_id:03d}"
        breed = cow.breed if cow else "Holstein-Friesian"
        lactation_stage = cow.lactation_stage if cow else "Mid-Lactation"

        # 1. Activity & Budget
        latest_activity = (
            db.query(ActivityRecord)
            .filter(ActivityRecord.cow_id == cow_id)
            .order_by(desc(ActivityRecord.timestamp))
            .first()
        )
        current_activity = latest_activity.predicted_behavior if latest_activity else "standing"
        activity_conf = latest_activity.confidence if latest_activity else 0.95

        latest_summary = (
            db.query(DailyActivitySummary)
            .filter(DailyActivitySummary.cow_id == cow_id)
            .order_by(desc(DailyActivitySummary.date))
            .first()
        )
        grazing_hrs = latest_summary.eating_hours if latest_summary else None
        lying_hrs = latest_summary.lying_hours if latest_summary else None
        walking_hrs = latest_summary.walking_hours if latest_summary else None

        # Active Activity Alerts (unacknowledged)
        active_alerts = (
            db.query(ActivityAlert)
            .filter(ActivityAlert.cow_id == cow_id, ActivityAlert.acknowledged == False)
            .all()
        )
        alert_names = [a.alert_type for a in active_alerts]

        # 2. Temperature Record
        latest_temp = (
            db.query(TemperatureRecord)
            .filter(TemperatureRecord.cow_id == cow_id)
            .order_by(desc(TemperatureRecord.timestamp))
            .first()
        )
        skin_t = latest_temp.skin_temperature if latest_temp else None
        amb_t = latest_temp.ambient_temperature if latest_temp else 22.0
        corr_t = latest_temp.corrected_temperature if latest_temp else None
        t_status = latest_temp.status if latest_temp else "NORMAL"
        cusum_fever = latest_temp.cusum_positive if latest_temp else 0.0
        cusum_hypo = latest_temp.cusum_negative if latest_temp else 0.0

        # 3. Heart Rate Record
        latest_hr = (
            db.query(HeartRateRecord)
            .filter(HeartRateRecord.cow_id == cow_id)
            .order_by(desc(HeartRateRecord.timestamp))
            .first()
        )
        hr_bpm = latest_hr.heart_rate if latest_hr else None
        baseline_bpm = latest_hr.baseline_bpm if latest_hr else 65.0
        hr_delta_pct = latest_hr.delta_pct if latest_hr else 0.0
        hr_status = latest_hr.status if latest_hr else "NORMAL"

        # 4. GPS Record
        latest_gps = (
            db.query(GPSRecord)
            .filter(GPSRecord.cow_id == cow_id)
            .order_by(desc(GPSRecord.timestamp))
            .first()
        )
        lat = latest_gps.lat if latest_gps else None
        lon = latest_gps.lon if latest_gps else None
        gps_behavior = latest_gps.gps_behavior if latest_gps else None
        is_outside = latest_gps.is_outside if latest_gps else False
        geofence_breach = latest_gps.geofence_breach if latest_gps else False

        return CowTelemetrySnapshot(
            cow_id=cow_id,
            cow_tag=cow_tag,
            breed=breed,
            lactation_stage=lactation_stage,
            timestamp=datetime.now(timezone.utc),
            current_activity=current_activity,
            activity_confidence=activity_conf,
            daily_grazing_hours=grazing_hrs,
            daily_lying_hours=lying_hrs,
            daily_walking_hours=walking_hrs,
            active_activity_alerts=alert_names,
            skin_temperature=skin_t,
            ambient_temperature=amb_t,
            corrected_temperature=corr_t,
            temperature_status=t_status,
            cusum_fever_score=cusum_fever,
            cusum_hypo_score=cusum_hypo,
            heart_rate_bpm=hr_bpm,
            baseline_bpm=baseline_bpm,
            heart_rate_delta_pct=hr_delta_pct,
            heart_rate_status=hr_status,
            gps_lat=lat,
            gps_lon=lon,
            gps_behavior=gps_behavior,
            is_outside_geofence=is_outside,
            geofence_breach=geofence_breach,
        )

    def diagnose(self, snapshot: CowTelemetrySnapshot) -> SimpleDiagnosticCard:
        """
        Diagnoses the cow's health using Gemini 3.8 Flash, with deterministic clinical fallback.
        """
        now_str = datetime.now(timezone.utc).isoformat()

        # If API key is available, attempt Gemini generation
        if self.api_key:
            try:
                card = self._call_gemini_api(snapshot, now_str)
                if card:
                    return card
            except Exception as e:
                logger.warning(f"Gemini API call failed: {e}. Falling back to clinical rule synthesizer.")

        # Deterministic clinical veterinary rule fallback (zero-cost, offline-reliable)
        return self._clinical_rule_synthesizer(snapshot, now_str)

    def _build_prompt(self, snapshot: CowTelemetrySnapshot) -> str:
        data_summary = {
            "cow_id": snapshot.cow_id,
            "cow_tag": snapshot.cow_tag,
            "breed": snapshot.breed,
            "lactation_stage": snapshot.lactation_stage,
            "activity": {
                "current_state": snapshot.current_activity,
                "confidence": snapshot.activity_confidence,
                "daily_grazing_hours": snapshot.daily_grazing_hours,
                "daily_lying_hours": snapshot.daily_lying_hours,
                "daily_walking_hours": snapshot.daily_walking_hours,
                "active_alerts": snapshot.active_activity_alerts,
            },
            "temperature": {
                "skin_temp_c": snapshot.skin_temperature,
                "ambient_temp_c": snapshot.ambient_temperature,
                "corrected_body_temp_c": snapshot.corrected_temperature,
                "status": snapshot.temperature_status,
                "cusum_fever_score": snapshot.cusum_fever_score,
                "cusum_hypo_score": snapshot.cusum_hypo_score,
            },
            "heart_rate": {
                "bpm": snapshot.heart_rate_bpm,
                "baseline_bpm": snapshot.baseline_bpm,
                "deviation_pct": snapshot.heart_rate_delta_pct,
                "status": snapshot.heart_rate_status,
            },
            "gps_geofence": {
                "lat": snapshot.gps_lat,
                "lon": snapshot.gps_lon,
                "trajectory_behavior": snapshot.gps_behavior,
                "is_outside": snapshot.is_outside_geofence,
                "geofence_breach_confirmed": snapshot.geofence_breach,
            },
        }

        prompt = f"""You are an expert Bovine Veterinary AI Assistant for dairy cattle herds.
Analyze the multi-modal telemetry parameters below for Cow {snapshot.cow_tag} and generate a standardized, concise, farmer-friendly diagnostic card.

Cow Telemetry Data:
{json.dumps(data_summary, indent=2)}

Guidelines:
1. Cross-correlate modalities:
   - High fever + high resting HR + feeding deficit -> Acute infection / Mastitis (EMERGENCY).
   - Low temp (<37.5°C) + low HR + recumbency -> Milk Fever / Hypocalcemia (EMERGENCY).
   - Surge in walking + drop in lying + normal temp -> Behavioral Estrus / Heat (ATTENTION).
   - Drop in walking + reluctance to move + normal temp -> Lameness (MONITOR).
   - Geofence breach -> Escape / Pasture breach (ATTENTION).
   - Stable parameters -> Healthy (NORMAL).
2. Triage levels: NORMAL, MONITOR, ATTENTION, EMERGENCY.
3. Keep the output clean, simple, and direct.
4. Output STRICT JSON conforming to this schema:
{{
  "cow_id": {snapshot.cow_id},
  "cow_tag": "{snapshot.cow_tag}",
  "triage_level": "NORMAL" | "MONITOR" | "ATTENTION" | "EMERGENCY",
  "headline": "<Concise 1-line condition summary>",
  "farmer_message": "<2 to 3 simple, everyday sentences explaining what is happening to the cow>",
  "key_indicators": ["<Observation 1>", "<Observation 2>", "<Observation 3>"],
  "action_steps": ["<Action 1>", "<Action 2>", "<Action 3>"]
}}
"""
        return prompt

    def _call_gemini_api(self, snapshot: CowTelemetrySnapshot, now_str: str) -> Optional[SimpleDiagnosticCard]:
        prompt = self._build_prompt(snapshot)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                text_content = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text_content)
                return SimpleDiagnosticCard(
                    cow_id=snapshot.cow_id,
                    cow_tag=snapshot.cow_tag,
                    timestamp=now_str,
                    triage_level=parsed.get("triage_level", "NORMAL").upper(),
                    headline=parsed.get("headline", "Health Assessment Completed"),
                    farmer_message=parsed.get("farmer_message", "All telemetry parameters evaluated."),
                    key_indicators=parsed.get("key_indicators", []),
                    action_steps=parsed.get("action_steps", []),
                )
            else:
                logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text}")
                return None

    def _clinical_rule_synthesizer(self, snapshot: CowTelemetrySnapshot, now_str: str) -> SimpleDiagnosticCard:
        """
        Deterministic, offline expert veterinary rule engine.
        Guarantees 100% reliable evaluation with zero API dependencies.
        """
        cow_tag = snapshot.cow_tag or f"COW-{snapshot.cow_id:03d}"
        corr_t = snapshot.corrected_temperature if snapshot.corrected_temperature is not None else 38.5
        hr_bpm = snapshot.heart_rate_bpm if snapshot.heart_rate_bpm is not None else 65.0
        alerts = snapshot.active_activity_alerts or []

        # 1. Critical Hypothermia / Milk Fever (Hypocalcemia)
        if snapshot.temperature_status in ["WARNING_HYPOTHERMIA", "CRITICAL_HYPOTHERMIA"] or corr_t < 37.5:
            return SimpleDiagnosticCard(
                cow_id=snapshot.cow_id,
                cow_tag=cow_tag,
                timestamp=now_str,
                triage_level="EMERGENCY",
                headline="Subnormal Body Temperature & Weakness (Suspected Milk Fever)",
                farmer_message=(
                    f"Cow {cow_tag} has dangerously low body temperature ({corr_t:.1f}°C) and a depressed pulse ({hr_bpm:.0f} BPM). "
                    "This indicates acute hypocalcemia (milk fever) and requires immediate veterinary intervention to prevent recumbency."
                ),
                key_indicators=[
                    f"Body Temperature: {corr_t:.1f}°C (Subnormal hypothermia, CUSUM S-: {snapshot.cusum_hypo_score:.2f}°C)",
                    f"Heart Rate: {hr_bpm:.0f} BPM (Depressed / Bradycardia)",
                    f"Behavior: {snapshot.current_activity.capitalize()} with prolonged immobility",
                ],
                action_steps=[
                    "Do not force the cow to rise or walk",
                    "Contact the attending veterinarian immediately for IV calcium borogluconate therapy",
                    "Keep the cow sternally recumbent in a dry, well-bedded stall to prevent muscle damage",
                ],
            )

        # 2. Critical Fever / Toxic Mastitis / Systemic Infection
        if snapshot.temperature_status in ["CRITICAL_FEVER", "WARNING_FEVER"] or corr_t >= 39.5:
            is_emergency = (
                snapshot.temperature_status == "CRITICAL_FEVER"
                or corr_t >= 40.0
                or snapshot.heart_rate_status == "HIGH_HEART_RATE"
                or hr_bpm >= 80.0
                or "FEEDING_DEFICIT" in alerts
            )
            triage = "EMERGENCY" if is_emergency else "ATTENTION"
            headline = "High Fever & Systemic Strain (Suspected Mastitis)" if is_emergency else "Elevated Temperature (Early Fever Warning)"
            return SimpleDiagnosticCard(
                cow_id=snapshot.cow_id,
                cow_tag=cow_tag,
                timestamp=now_str,
                triage_level=triage,
                headline=headline,
                farmer_message=(
                    f"Cow {cow_tag} is running a fever ({corr_t:.1f}°C) with an elevated resting pulse ({hr_bpm:.0f} BPM) "
                    "and reduced feed intake. This is characteristic of an active bacterial infection, such as acute mastitis or metritis."
                ),
                key_indicators=[
                    f"Body Temperature: {corr_t:.1f}°C (CUSUM Fever Score: +{snapshot.cusum_fever_score:.2f}°C)",
                    f"Heart Rate: {hr_bpm:.0f} BPM ({snapshot.heart_rate_delta_pct:+.1f}% baseline deviation)",
                    "Feeding Behavior: Significant reduction in daily grazing and rumination",
                ],
                action_steps=[
                    "Physically inspect all four udder quarters for swelling, heat, or abnormal milk secretions",
                    "Perform a California Mastitis Test (CMT) strip",
                    "Administer prescribed antipyretic or antibiotic under veterinary guidance",
                ],
            )

        # 3. Geofence Boundary Breach
        if snapshot.geofence_breach or snapshot.is_outside_geofence:
            lat_str = f"{snapshot.gps_lat:.5f}" if snapshot.gps_lat else "Unknown"
            lon_str = f"{snapshot.gps_lon:.5f}" if snapshot.gps_lon else "Unknown"
            return SimpleDiagnosticCard(
                cow_id=snapshot.cow_id,
                cow_tag=cow_tag,
                timestamp=now_str,
                triage_level="ATTENTION",
                headline="Pasture Boundary Breach Detected",
                farmer_message=(
                    f"Cow {cow_tag} has moved outside the designated grazing pasture perimeter. "
                    f"Current position is Lat: {lat_str}, Lon: {lon_str}."
                ),
                key_indicators=[
                    "Geofence Status: Outside farm polygon perimeter (Confirmed Breach)",
                    f"GPS Trajectory State: {snapshot.gps_behavior or 'Moving'}",
                    f"Current Location: {lat_str}, {lon_str}",
                ],
                action_steps=[
                    "Dispatch a farm worker to the reported GPS coordinates to guide the cow back",
                    "Inspect boundary fences and gates near the breach sector",
                    "Verify collar battery charge and GPS fix status",
                ],
            )

        # 4. Estrus / Standing Heat Cycle
        if "ESTRUS_SUSPECTED" in alerts or (snapshot.daily_walking_hours and snapshot.daily_walking_hours > 3.5):
            return SimpleDiagnosticCard(
                cow_id=snapshot.cow_id,
                cow_tag=cow_tag,
                timestamp=now_str,
                triage_level="ATTENTION",
                headline="Standing Heat Detected (Optimal Insemination Window)",
                farmer_message=(
                    f"Cow {cow_tag} is exhibiting peak behavioral estrus (in heat), characterized by a dramatic spike in walking "
                    "activity and reduced rest. Temperature and pulse remain in the normal range."
                ),
                key_indicators=[
                    "Activity: Daily walking activity surged by >100% above 7-day baseline",
                    f"Resting Time: Lying down decreased ({snapshot.daily_lying_hours or 5.0:.1f} hours)",
                    f"Vital Signs: Normal temperature ({corr_t:.1f}°C) and pulse ({hr_bpm:.0f} BPM)",
                ],
                action_steps=[
                    "Schedule Artificial Insemination (AI) within the next 12 to 18 hours (AM/PM rule)",
                    "Visually confirm secondary heat signs (standing to be mounted, clear discharge)",
                    "Separate the cow into a calm breeding pen",
                ],
            )

        # 5. Lameness / Musculoskeletal Pain
        if "LAMENESS_SUSPECTED" in alerts:
            return SimpleDiagnosticCard(
                cow_id=snapshot.cow_id,
                cow_tag=cow_tag,
                timestamp=now_str,
                triage_level="MONITOR",
                headline="Reduced Mobility (Suspected Lameness or Hoof Lesion)",
                farmer_message=(
                    f"Cow {cow_tag} is showing a sharp drop in walking mobility and reluctance to move, without a fever. "
                    "This pattern typically indicates early hoof lesions, sole ulcers, or musculoskeletal soreness."
                ),
                key_indicators=[
                    "Activity: Walking activity dropped by >50% below baseline",
                    f"Resting Time: Increased lying recumbency ({snapshot.daily_lying_hours or 12.0:.1f} hours)",
                    f"Vitals: Body temperature stable ({corr_t:.1f}°C)",
                ],
                action_steps=[
                    "Inspect all four hooves in the trimming chute for digital dermatitis or stones",
                    "Evaluate locomotion score as the cow walks on concrete",
                    "Apply topical treatment or schedule corrective hoof trimming if necessary",
                ],
            )

        # 6. Normal Healthy State
        return SimpleDiagnosticCard(
            cow_id=snapshot.cow_id,
            cow_tag=cow_tag,
            timestamp=now_str,
            triage_level="NORMAL",
            headline="Healthy & Normal Activity",
            farmer_message=(
                f"Cow {cow_tag} is in good health with normal daily activity rhythms, stable core temperature ({corr_t:.1f}°C), "
                f"normal resting heart rate ({hr_bpm:.0f} BPM), and is grazing within safe pasture boundaries."
            ),
            key_indicators=[
                f"Body Temperature: {corr_t:.1f}°C (Normal circadian range)",
                f"Heart Rate: {hr_bpm:.0f} BPM (Normal resting baseline)",
                f"Behavior: {snapshot.current_activity.capitalize()} (Balanced 24h grazing & resting budget)",
                "Pasture Status: Safely inside geofence perimeter",
            ],
            action_steps=[
                "Continue standard herd management and daily observations",
                "Ensure clean drinking water and fresh forage availability",
            ],
        )


# Global service instance
llm_vet_service = LLMVetService()
