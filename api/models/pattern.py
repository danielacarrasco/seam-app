from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from api.database import Base


class Pattern(Base):
    __tablename__ = "patterns"

    id = Column(Integer, primary_key=True)
    brand = Column(String(120))
    designer = Column(String(120))
    pattern_name = Column(String(200), nullable=False)
    pattern_number = Column(String(80))
    garment_type = Column(String(40))
    size_chosen = Column(String(40))
    size_range = Column(String(80))
    view_version = Column(String(80))
    recommended_fabrics = Column(Text)
    instructions_rating = Column(Integer)
    notes = Column(Text)
    image_path = Column(String(300))
    previously_used = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    projects = relationship("Project", back_populates="pattern")
    fit_history = relationship(
        "FitHistoryEntry",
        back_populates="pattern",
        cascade="all, delete-orphan",
        order_by="desc(FitHistoryEntry.created_at)",
    )
    makes = relationship("Make", back_populates="pattern")


class FitHistoryEntry(Base):
    __tablename__ = "fit_history_entries"

    id = Column(Integer, primary_key=True)
    pattern_id = Column(
        Integer, ForeignKey("patterns.id", ondelete="CASCADE"), nullable=False
    )
    alterations_made = Column(Text)
    fit_notes = Column(Text)
    size_used = Column(String(40))
    linked_make_id = Column(
        Integer, ForeignKey("makes.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    pattern = relationship("Pattern", back_populates="fit_history")
