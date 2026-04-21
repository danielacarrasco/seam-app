from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from api.database import get_db
from api.models import (
    Fabric,
    Pattern,
    ProgressLogEntry,
    Project,
    ProjectFabric,
)
from api.schemas import (
    ProgressLogEntryCreate,
    ProgressLogEntryRead,
    ProjectCreate,
    ProjectRead,
    ProjectSummary,
    ProjectUpdate,
)
from api.schemas.fabric import FabricSummary
from api.storage import media_url

router = APIRouter()


def _hydrate(project: Project) -> Project:
    """Attach computed fields (linked fabrics with photo_url) to a project."""
    fabrics = []
    for link in project.fabric_links:
        f = link.fabric
        f.photo_url = media_url(f.photo_path)
        fabrics.append(f)
    project.fabrics = fabrics
    return project


@router.get("/", response_model=List[ProjectSummary])
def list_projects(
    status: Optional[str] = None,
    garment_type: Optional[str] = None,
    season: Optional[str] = None,
    priority: Optional[str] = None,
    fabric_id: Optional[int] = None,
    pattern_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Project)
    if status:
        q = q.filter(Project.status == status)
    if garment_type:
        q = q.filter(Project.garment_type == garment_type)
    if season:
        q = q.filter(Project.season == season)
    if priority:
        q = q.filter(Project.priority == priority)
    if pattern_id is not None:
        q = q.filter(Project.pattern_id == pattern_id)
    if fabric_id is not None:
        q = q.join(Project.fabric_links).filter(ProjectFabric.fabric_id == fabric_id)
    return q.order_by(Project.created_at.desc()).all()


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    project = Project(**data)
    db.add(project)
    db.commit()
    db.refresh(project)
    return _hydrate(project)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")
    return _hydrate(project)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return _hydrate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")
    db.delete(project)
    db.commit()
    return None


# --- Fabric links ---

@router.post("/{project_id}/fabrics/{fabric_id}", status_code=status.HTTP_201_CREATED)
def link_fabric(project_id: int, fabric_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    fabric = db.get(Fabric, fabric_id)
    if not project or not fabric:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project or fabric not found")
    existing = (
        db.query(ProjectFabric)
        .filter_by(project_id=project_id, fabric_id=fabric_id)
        .first()
    )
    if existing:
        return {"status": "already_linked"}
    db.add(ProjectFabric(project_id=project_id, fabric_id=fabric_id))
    db.commit()
    return {"status": "linked"}


@router.delete(
    "/{project_id}/fabrics/{fabric_id}", status_code=status.HTTP_204_NO_CONTENT
)
def unlink_fabric(project_id: int, fabric_id: int, db: Session = Depends(get_db)):
    link = (
        db.query(ProjectFabric)
        .filter_by(project_id=project_id, fabric_id=fabric_id)
        .first()
    )
    if link:
        db.delete(link)
        db.commit()
    return None


# --- Pattern link ---

@router.put("/{project_id}/pattern/{pattern_id}", response_model=ProjectRead)
def set_pattern(project_id: int, pattern_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    pattern = db.get(Pattern, pattern_id)
    if not project or not pattern:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project or pattern not found")
    project.pattern_id = pattern_id
    db.commit()
    db.refresh(project)
    return _hydrate(project)


@router.delete("/{project_id}/pattern", status_code=status.HTTP_204_NO_CONTENT)
def remove_pattern(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")
    project.pattern_id = None
    db.commit()
    return None


# --- Progress log ---

@router.get("/{project_id}/log", response_model=List[ProgressLogEntryRead])
def get_progress_log(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")
    return project.progress_log


@router.post(
    "/{project_id}/log",
    response_model=ProgressLogEntryRead,
    status_code=status.HTTP_201_CREATED,
)
def add_log_entry(
    project_id: int,
    payload: ProgressLogEntryCreate,
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")
    entry = ProgressLogEntry(project_id=project_id, note=payload.note)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete(
    "/{project_id}/log/{entry_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_log_entry(project_id: int, entry_id: int, db: Session = Depends(get_db)):
    entry = (
        db.query(ProgressLogEntry)
        .filter_by(id=entry_id, project_id=project_id)
        .first()
    )
    if entry:
        db.delete(entry)
        db.commit()
    return None
