from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class FabricBase(BaseModel):
    nickname: Optional[str] = None
    fiber_content: Optional[str] = None
    color: Optional[str] = None
    print_pattern: Optional[str] = None
    length_meters: Optional[float] = None
    width_cm: Optional[float] = None
    weight_gsm: Optional[float] = None
    stretch: Optional[bool] = None
    drape_structure: Optional[str] = None
    opacity: Optional[str] = None
    care_instructions: Optional[str] = None
    source_store: Optional[str] = None
    cost: Optional[float] = None
    date_acquired: Optional[date] = None
    suitable_garment_types: Optional[List[str]] = None
    notes: Optional[str] = None


class FabricCreate(FabricBase):
    nickname: str = Field(..., min_length=1, max_length=200)


class FabricUpdate(FabricBase):
    reserved: Optional[bool] = None


class _ReservedProjectRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str


class FabricSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: str
    fiber_content: Optional[str] = None
    color: Optional[str] = None
    length_meters: Optional[float] = None
    reserved: bool
    photo_url: Optional[str] = None


class FabricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: str
    fiber_content: Optional[str] = None
    color: Optional[str] = None
    print_pattern: Optional[str] = None
    length_meters: Optional[float] = None
    width_cm: Optional[float] = None
    weight_gsm: Optional[float] = None
    stretch: bool
    drape_structure: Optional[str] = None
    opacity: Optional[str] = None
    care_instructions: Optional[str] = None
    source_store: Optional[str] = None
    cost: Optional[float] = None
    date_acquired: Optional[date] = None
    suitable_garment_types: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    reserved: bool
    reserved_project: Optional[_ReservedProjectRef] = None
    created_at: datetime
    updated_at: datetime
