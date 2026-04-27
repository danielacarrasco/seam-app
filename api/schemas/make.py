from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class _ProjectRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str


class _PatternRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    pattern_name: str


class _FabricRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nickname: str


class MakeBase(BaseModel):
    project_id: Optional[int] = None
    fabric_id: Optional[int] = None
    pattern_id: Optional[int] = None
    construction_notes: Optional[str] = None
    fit_outcome: Optional[str] = None
    what_worked: Optional[str] = None
    what_didnt: Optional[str] = None
    would_remake: Optional[bool] = None
    wear_frequency: Optional[str] = None
    care_outcome: Optional[str] = None
    lessons_learned: Optional[str] = None
    rating: Optional[float] = Field(default=None, ge=1, le=7)


class MakeCreate(MakeBase):
    pass


class MakeUpdate(MakeBase):
    pass


class MakePhotoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    url: str


class MakeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fit_outcome: Optional[str] = None
    would_remake: bool
    rating: Optional[float] = None
    created_at: datetime
    project: Optional[_ProjectRef] = None
    cover_photo_url: Optional[str] = None


class MakeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    construction_notes: Optional[str] = None
    fit_outcome: Optional[str] = None
    what_worked: Optional[str] = None
    what_didnt: Optional[str] = None
    would_remake: bool
    wear_frequency: Optional[str] = None
    care_outcome: Optional[str] = None
    lessons_learned: Optional[str] = None
    rating: Optional[float] = None
    project: Optional[_ProjectRef] = None
    pattern: Optional[_PatternRef] = None
    fabric: Optional[_FabricRef] = None
    created_at: datetime
    updated_at: datetime
