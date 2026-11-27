from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CowBase(BaseModel):
    tag_id: str = Field(..., description="Unique collar ear tag / ID, e.g. COW_01")
    name: Optional[str] = Field(None, description="Optional cow nickname")
    breed: Optional[str] = Field("Holstein-Friesian", description="Cow breed")
    age_months: Optional[int] = Field(None, description="Age in months")
    lactation_stage: Optional[str] = Field("Mid-Lactation", description="Current lactation cycle stage")
    collar_battery_pct: Optional[float] = Field(100.0, ge=0.0, le=100.0)

class CowCreate(CowBase):
    pass

class CowResponse(CowBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
