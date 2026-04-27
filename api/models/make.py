from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from api.database import Base


class Make(Base):
    __tablename__ = "makes"

    id = Column(Integer, primary_key=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    fabric_id = Column(
        Integer, ForeignKey("fabrics.id", ondelete="SET NULL"), nullable=True
    )
    pattern_id = Column(
        Integer, ForeignKey("patterns.id", ondelete="SET NULL"), nullable=True
    )

    construction_notes = Column(Text)
    fit_outcome = Column(String(30))
    what_worked = Column(Text)
    what_didnt = Column(Text)
    would_remake = Column(Boolean, default=False, nullable=False)
    wear_frequency = Column(String(20))
    care_outcome = Column(Text)
    lessons_learned = Column(Text)
    rating = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    project = relationship("Project", back_populates="makes")
    fabric = relationship("Fabric")
    pattern = relationship("Pattern", back_populates="makes")
    photos = relationship(
        "MakePhoto",
        back_populates="make",
        cascade="all, delete-orphan",
        order_by="MakePhoto.created_at",
    )


class MakePhoto(Base):
    __tablename__ = "make_photos"

    id = Column(Integer, primary_key=True)
    make_id = Column(
        Integer, ForeignKey("makes.id", ondelete="CASCADE"), nullable=False
    )
    path = Column(String(300), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    make = relationship("Make", back_populates="photos")
