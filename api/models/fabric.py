from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    Date,
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


class Fabric(Base):
    __tablename__ = "fabrics"

    id = Column(Integer, primary_key=True)
    nickname = Column(String(200), nullable=False)
    fiber_content = Column(String(200))
    color = Column(String(80))
    print_pattern = Column(String(120))
    length_meters = Column(Float)
    width_cm = Column(Float)
    weight_gsm = Column(Float)
    stretch = Column(Boolean, default=False, nullable=False)
    drape_structure = Column(String(40))
    opacity = Column(String(40))
    care_instructions = Column(Text)
    source_store = Column(String(200))
    cost = Column(Float)
    date_acquired = Column(Date)
    suitable_garment_types = Column(JSON, default=list)
    notes = Column(Text)
    photo_path = Column(String(300))

    reserved = Column(Boolean, default=False, nullable=False)
    reserved_project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    reserved_project = relationship(
        "Project",
        foreign_keys=[reserved_project_id],
        back_populates="reservations",
    )
    project_links = relationship(
        "ProjectFabric", back_populates="fabric", cascade="all, delete-orphan"
    )
