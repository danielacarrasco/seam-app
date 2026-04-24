from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from api.database import Base


MEASUREMENT_FIELDS = (
    "bust",
    "waist",
    "hips",
    "high_bust",
    "back_length",
    "front_length",
    "shoulder_width",
    "sleeve_length",
    "inseam",
    "rise",
    "neck",
    "upper_arm",
    "wrist",
    "thigh",
    "calf",
    "height",
    "weight",
)


class MeasurementProfile(Base):
    __tablename__ = "measurement_profile"

    # Single-row table. id is pinned to 1 by the router logic.
    id = Column(Integer, primary_key=True)

    bust = Column(Float)
    waist = Column(Float)
    hips = Column(Float)
    high_bust = Column(Float)
    back_length = Column(Float)
    front_length = Column(Float)
    shoulder_width = Column(Float)
    sleeve_length = Column(Float)
    inseam = Column(Float)
    rise = Column(Float)
    neck = Column(Float)
    upper_arm = Column(Float)
    wrist = Column(Float)
    thigh = Column(Float)
    calf = Column(Float)
    height = Column(Float)
    weight = Column(Float)

    preferred_ease = Column(String(120))
    fit_notes = Column(Text)

    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class MeasurementSnapshot(Base):
    __tablename__ = "measurement_snapshots"

    id = Column(Integer, primary_key=True)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Alteration(Base):
    __tablename__ = "alterations"

    id = Column(Integer, primary_key=True)
    label = Column(String(200), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FitNote(Base):
    __tablename__ = "fit_notes"

    id = Column(Integer, primary_key=True)
    garment_type = Column(String(40), nullable=False)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
