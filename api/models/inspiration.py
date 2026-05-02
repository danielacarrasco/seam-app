from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
)

from api.database import Base


class InspirationEntry(Base):
    __tablename__ = "inspiration_entries"

    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    entry_type = Column(String(20), nullable=False, default="note")
    body = Column(Text)
    tags = Column(JSON, default=list)
    image_path = Column(String(300))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class InspirationProjectSuggestion(Base):
    __tablename__ = "inspiration_project_suggestions"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    source_entry_ids = Column(JSON, nullable=False, default=list)
    garment_type = Column(String(40))
    silhouette = Column(String(80))
    mood = Column(JSON, default=list)
    palette = Column(JSON, default=list)
    imagery = Column(JSON, default=list)
    fabric_ideas = Column(JSON, default=list)
    pattern_features = Column(JSON, default=list)
    construction_notes = Column(JSON, default=list)
    fit_considerations = Column(JSON, default=list)
    sketch_prompt = Column(Text)
    rationale = Column(Text)
    raw_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
