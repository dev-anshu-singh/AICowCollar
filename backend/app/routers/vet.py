from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.cow import Cow
from ..schemas.vet import CowTelemetrySnapshot, SimpleDiagnosticCard
from ..services.llm_vet_service import llm_vet_service

vet_router = APIRouter(tags=["Veterinary AI Assistant"])


@vet_router.get(
    "/cows/{cow_id}/vet-diagnosis",
    response_model=SimpleDiagnosticCard,
    summary="Get unified veterinary clinical diagnostic card for a cow",
    description=(
        "Collects multi-modal telemetry across Activity, Temperature, Pulse, and GPS "
        "and produces a simple, farmer-friendly diagnostic card using Gemini 3.8 Flash."
    ),
)
def get_cow_vet_diagnosis(cow_id: int, db: Session = Depends(get_db)):
    cow = db.query(Cow).filter(Cow.id == cow_id).first()
    if not cow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cow with id {cow_id} not found."
        )

    snapshot = llm_vet_service.extract_cow_snapshot(db, cow_id)
    card = llm_vet_service.diagnose(snapshot)
    return card


@vet_router.post(
    "/vet/diagnose",
    response_model=SimpleDiagnosticCard,
    summary="Simulate / diagnose ad-hoc multi-sensor cow parameters",
    description=(
        "Directly analyzes an ad-hoc or simulated multi-sensor telemetry snapshot "
        "and returns the standardized Simple Diagnostic Card."
    ),
)
def diagnose_telemetry_snapshot(snapshot: CowTelemetrySnapshot):
    card = llm_vet_service.diagnose(snapshot)
    return card
