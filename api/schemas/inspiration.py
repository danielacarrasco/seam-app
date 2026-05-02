from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


ENTRY_TYPES = (
    "dream",
    "thought",
    "memory",
    "mood",
    "image",
    "fabric",
    "silhouette",
    "note",
)


class InspirationEntryBase(BaseModel):
    title: Optional[str] = None
    entry_type: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[List[str]] = None


class InspirationEntryCreate(InspirationEntryBase):
    entry_type: str = "note"
    # body or image required, validated by router after image upload step


class InspirationEntryUpdate(InspirationEntryBase):
    pass


class InspirationEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: Optional[str] = None
    entry_type: str
    body: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class GenerateSuggestionRequest(BaseModel):
    entry_ids: List[int] = Field(..., min_length=1)


class InspirationSuggestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source_entry_ids: List[int] = Field(default_factory=list)
    garment_type: Optional[str] = None
    silhouette: Optional[str] = None
    mood: List[str] = Field(default_factory=list)
    palette: List[str] = Field(default_factory=list)
    imagery: List[str] = Field(default_factory=list)
    fabric_ideas: List[str] = Field(default_factory=list)
    pattern_features: List[str] = Field(default_factory=list)
    construction_notes: List[str] = Field(default_factory=list)
    fit_considerations: List[str] = Field(default_factory=list)
    sketch_prompt: Optional[str] = None
    rationale: Optional[str] = None
    created_at: datetime
