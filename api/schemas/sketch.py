from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SketchGenerate(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    project_id: Optional[int] = None


class SketchUpdate(BaseModel):
    project_id: Optional[int] = None


class _ProjectRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str


class SketchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    prompt: Optional[str] = None
    url: str
    project: Optional[_ProjectRef] = None
    created_at: datetime
