from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PatternBase(BaseModel):
    brand: Optional[str] = None
    designer: Optional[str] = None
    pattern_name: Optional[str] = None
    pattern_number: Optional[str] = None
    garment_type: Optional[str] = None
    size_chosen: Optional[str] = None
    size_range: Optional[str] = None
    view_version: Optional[str] = None
    recommended_fabrics: Optional[str] = None
    instructions_rating: Optional[int] = Field(default=None, ge=1, le=5)
    notes: Optional[str] = None


class PatternCreate(PatternBase):
    pattern_name: str = Field(..., min_length=1, max_length=200)


class PatternUpdate(PatternBase):
    previously_used: Optional[bool] = None


class PatternSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pattern_name: str
    brand: Optional[str] = None
    garment_type: Optional[str] = None
    previously_used: bool


class PatternRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brand: Optional[str] = None
    designer: Optional[str] = None
    pattern_name: str
    pattern_number: Optional[str] = None
    garment_type: Optional[str] = None
    size_chosen: Optional[str] = None
    size_range: Optional[str] = None
    view_version: Optional[str] = None
    recommended_fabrics: Optional[str] = None
    instructions_rating: Optional[int] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None
    previously_used: bool
    created_at: datetime
    updated_at: datetime


class FitHistoryEntryCreate(BaseModel):
    alterations_made: Optional[str] = None
    fit_notes: Optional[str] = None
    size_used: Optional[str] = None
    linked_make_id: Optional[int] = None


class FitHistoryEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pattern_id: int
    alterations_made: Optional[str] = None
    fit_notes: Optional[str] = None
    size_used: Optional[str] = None
    linked_make_id: Optional[int] = None
    created_at: datetime
