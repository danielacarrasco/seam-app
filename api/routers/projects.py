from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from api.database import get_db

router = APIRouter()


@router.get("/")
def list_projects(
    status: Optional[str] = None,
    garment_type: Optional[str] = None,
    season: Optional[str] = None,
    priority: Optional[str] = None,
    fabric_id: Optional[int] = None,
    pattern_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    List all projects with optional filters.
    Supports filtering by status, garment_type, season, priority,
    linked fabric_id, and linked pattern_id.
    """
    return []


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_project(db: Session = Depends(get_db)):
    """
    Create a new project.
    Accepts title, garment_type, category_tags, status, occasion,
    season, difficulty, priority, estimated_meterage, notes,
    planned_techniques, fit_considerations.
    Status defaults to 'idea' if not provided.
    """
    return {}


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    """
    Get a single project by ID, including linked fabrics,
    pattern, sketches, inspiration images, and progress log.
    """
    project = None  # replace with db lookup
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return project


@router.patch("/{project_id}")
def update_project(project_id: int, db: Session = Depends(get_db)):
    """
    Partially update a project.
    All fields are optional — only provided fields are updated.
    Use this to update status, notes, progress, etc.
    """
    project = None  # replace with db lookup
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """
    Delete a project. Does not delete linked fabrics or patterns —
    only removes the project and its direct associations.
    """
    project = None  # replace with db lookup
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return None


# --- Fabric links ---

@router.post("/{project_id}/fabrics/{fabric_id}", status_code=status.HTTP_201_CREATED)
def link_fabric(project_id: int, fabric_id: int, db: Session = Depends(get_db)):
    """
    Link a fabric to a project.
    A project can have many linked fabrics (main, lining, interfacing, etc.).
    """
    return {}


@router.delete("/{project_id}/fabrics/{fabric_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_fabric(project_id: int, fabric_id: int, db: Session = Depends(get_db)):
    """Remove a fabric link from a project."""
    return None


# --- Pattern link ---

@router.put("/{project_id}/pattern/{pattern_id}")
def set_pattern(project_id: int, pattern_id: int, db: Session = Depends(get_db)):
    """
    Set or replace the pattern linked to a project.
    A project has at most one main pattern.
    """
    return {}


@router.delete("/{project_id}/pattern", status_code=status.HTTP_204_NO_CONTENT)
def remove_pattern(project_id: int, db: Session = Depends(get_db)):
    """Remove the pattern link from a project."""
    return None


# --- Progress log ---

@router.get("/{project_id}/log")
def get_progress_log(project_id: int, db: Session = Depends(get_db)):
    """Return all progress log entries for a project, newest first."""
    return []


@router.post("/{project_id}/log", status_code=status.HTTP_201_CREATED)
def add_log_entry(project_id: int, db: Session = Depends(get_db)):
    """
    Add a dated progress log entry to a project.
    Accepts a note (text) and optional photo.
    Timestamp is set automatically.
    """
    return {}


@router.delete("/{project_id}/log/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_log_entry(project_id: int, entry_id: int, db: Session = Depends(get_db)):
    """Delete a single progress log entry."""
    return None
