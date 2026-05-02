from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from api.database import Base


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    entry_type = Column(String(20), nullable=False, default="thought")
    body = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    image_path = Column(String(300))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    suggestions = relationship(
        "JournalProjectSuggestion",
        back_populates="entry",
        cascade="all, delete-orphan",
        order_by="JournalProjectSuggestion.created_at.desc()",
    )


class JournalProjectSuggestion(Base):
    __tablename__ = "journal_project_suggestions"

    id = Column(Integer, primary_key=True)
    journal_entry_id = Column(
        Integer, ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(200), nullable=False)
    garment_type = Column(String(40))
    silhouette = Column(String(80))
    mood = Column(JSON, default=list)
    palette = Column(JSON, default=list)
    fabric_ideas = Column(JSON, default=list)
    pattern_features = Column(JSON, default=list)
    construction_notes = Column(JSON, default=list)
    sketch_prompt = Column(Text)
    rationale = Column(Text)
    raw_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    entry = relationship("JournalEntry", back_populates="suggestions")
