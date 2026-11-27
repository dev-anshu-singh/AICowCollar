from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Cow
from ..schemas.cow import CowCreate, CowResponse

router = APIRouter(prefix="/cows", tags=["Cattle Management"])

@router.post("/", response_model=CowResponse, status_code=status.HTTP_201_CREATED)
def register_cow(cow_in: CowCreate, db: Session = Depends(get_db)):
    """
    Registers a new cow collar tag in the database.
    """
    existing = db.query(Cow).filter(Cow.tag_id == cow_in.tag_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cow with tag_id '{cow_in.tag_id}' is already registered (id: {existing.id})."
        )
    cow = Cow(**cow_in.model_dump())
    db.add(cow)
    db.commit()
    db.refresh(cow)
    return cow

@router.get("/", response_model=List[CowResponse])
def list_cows(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Lists all registered cows with battery levels and lactation status.
    """
    return db.query(Cow).offset(skip).limit(limit).all()

@router.get("/{cow_id}", response_model=CowResponse)
def get_cow(cow_id: int, db: Session = Depends(get_db)):
    """
    Retrieves specific cow details by ID.
    """
    cow = db.query(Cow).filter(Cow.id == cow_id).first()
    if not cow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cow not found.")
    return cow
