from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class _MeasurementFields(BaseModel):
    bust: Optional[float] = None
    waist: Optional[float] = None
    hips: Optional[float] = None
    high_bust: Optional[float] = None
    back_length: Optional[float] = None
    front_length: Optional[float] = None
    shoulder_width: Optional[float] = None
    sleeve_length: Optional[float] = None
    inseam: Optional[float] = None
    rise: Optional[float] = None
    neck: Optional[float] = None
    upper_arm: Optional[float] = None
    wrist: Optional[float] = None
    thigh: Optional[float] = None
    calf: Optional[float] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    preferred_ease: Optional[str] = None
    fit_notes: Optional[str] = None


class MeasurementProfileWrite(_MeasurementFields):
    pass


class MeasurementProfilePatch(_MeasurementFields):
    pass


class MeasurementProfileRead(_MeasurementFields):
    model_config = ConfigDict(from_attributes=True)
    updated_at: Optional[datetime] = None


class MeasurementSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    data: Dict[str, Any]
    created_at: datetime


class AlterationCreate(BaseModel):
    label: str
    notes: Optional[str] = None


class AlterationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    label: str
    notes: Optional[str] = None
    created_at: datetime


class FitNoteCreate(BaseModel):
    garment_type: str
    note: str


class FitNoteUpdate(BaseModel):
    garment_type: Optional[str] = None
    note: Optional[str] = None


class FitNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    garment_type: str
    note: str
    created_at: datetime
    updated_at: datetime
