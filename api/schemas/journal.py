from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


ENTRY_TYPES = ("dream", "thought", "memory", "inspiration", "mood")


class JournalEntryBase(BaseModel):
    title: Optional[str] = None
    entry_type: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[List[str]] = None


class JournalEntryCreate(JournalEntryBase):
    body: str = Field(..., min_length=1)
    entry_type: str = "thought"


class JournalEntryUpdate(JournalEntryBase):
    pass


class JournalSuggestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    journal_entry_id: int
    title: str
    garment_type: Optional[str] = None
    silhouette: Optional[str] = None
    mood: List[str] = Field(default_factory=list)
    palette: List[str] = Field(default_factory=list)
    fabric_ideas: List[str] = Field(default_factory=list)
    pattern_features: List[str] = Field(default_factory=list)
    construction_notes: List[str] = Field(default_factory=list)
    sketch_prompt: Optional[str] = None
    rationale: Optional[str] = None
    created_at: datetime


class JournalEntrySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: Optional[str] = None
    entry_type: str
    body: str
    tags: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    suggestion_count: int = 0
    created_at: datetime


class JournalEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: Optional[str] = None
    entry_type: str
    body: str
    tags: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    suggestions: List[JournalSuggestionRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
