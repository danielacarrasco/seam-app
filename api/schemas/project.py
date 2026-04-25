from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from api.schemas.fabric import FabricSummary


class ProjectBase(BaseModel):
    title: Optional[str] = None
    garment_type: Optional[str] = None
    category_tags: Optional[List[str]] = None
    status: Optional[str] = None
    occasion: Optional[str] = None
    season: Optional[str] = None
    difficulty: Optional[str] = None
    priority: Optional[str] = None
    estimated_meterage: Optional[float] = None
    notes: Optional[str] = None
    planned_techniques: Optional[str] = None
    fit_considerations: Optional[str] = None


class ProjectCreate(ProjectBase):
    title: str = Field(..., min_length=1, max_length=200)
    status: str = "idea"


class ProjectUpdate(ProjectBase):
    pass


class _PatternRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    pattern_name: str
    brand: Optional[str] = None
    size_chosen: Optional[str] = None


class ProjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    garment_type: Optional[str] = None
    status: str
    season: Optional[str] = None
    priority: Optional[str] = None
    created_at: datetime
    thumbnail_url: Optional[str] = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    garment_type: Optional[str] = None
    category_tags: List[str] = Field(default_factory=list)
    status: str
    occasion: Optional[str] = None
    season: Optional[str] = None
    difficulty: Optional[str] = None
    priority: Optional[str] = None
    estimated_meterage: Optional[float] = None
    notes: Optional[str] = None
    planned_techniques: Optional[str] = None
    fit_considerations: Optional[str] = None
    fabrics: List[FabricSummary] = Field(default_factory=list)
    pattern: Optional[_PatternRef] = None
    created_at: datetime
    updated_at: datetime


class ProgressLogEntryCreate(BaseModel):
    note: str = Field(..., min_length=1)


class ProgressLogEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    note: str
    photo_path: Optional[str] = None
    created_at: datetime
