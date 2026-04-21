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
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from api.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    garment_type = Column(String(40))
    category_tags = Column(JSON, default=list)
    status = Column(String(20), nullable=False, default="idea")
    occasion = Column(String(120))
    season = Column(String(20))
    difficulty = Column(String(20))
    priority = Column(String(20), default="medium")
    estimated_meterage = Column(Float)
    notes = Column(Text)
    planned_techniques = Column(Text)
    fit_considerations = Column(Text)

    pattern_id = Column(
        Integer, ForeignKey("patterns.id", ondelete="SET NULL"), nullable=True
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    pattern = relationship("Pattern", back_populates="projects")
    fabric_links = relationship(
        "ProjectFabric", back_populates="project", cascade="all, delete-orphan"
    )
    progress_log = relationship(
        "ProgressLogEntry",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(ProgressLogEntry.created_at)",
    )
    reservations = relationship(
        "Fabric",
        foreign_keys="Fabric.reserved_project_id",
        back_populates="reserved_project",
    )
    makes = relationship("Make", back_populates="project")


class ProjectFabric(Base):
    __tablename__ = "project_fabrics"
    __table_args__ = (
        UniqueConstraint("project_id", "fabric_id", name="uq_project_fabric"),
    )

    id = Column(Integer, primary_key=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    fabric_id = Column(
        Integer, ForeignKey("fabrics.id", ondelete="CASCADE"), nullable=False
    )

    project = relationship("Project", back_populates="fabric_links")
    fabric = relationship("Fabric", back_populates="project_links")


class ProgressLogEntry(Base):
    __tablename__ = "progress_log_entries"

    id = Column(Integer, primary_key=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    note = Column(Text, nullable=False)
    photo_path = Column(String(300))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="progress_log")
