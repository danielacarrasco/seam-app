from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from api.database import get_db

router = APIRouter()


@router.get("/")
def list_fabrics(
    fiber: Optional[str] = None,
    color: Optional[str] = None,
    stretch: Optional[bool] = None,
    structure: Optional[str] = None,
    reserved: Optional[bool] = None,
    suitable_for: Optional[str] = None,
    min_length: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """
    List all fabrics in the stash with optional filters.
    suitable_for accepts a garment type string (e.g. 'coat', 'dress')
    and returns fabrics tagged as suitable for that type.
    reserved=True returns only reserved fabrics, False returns only available ones.
    """
    return []


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_fabric(db: Session = Depends(get_db)):
    """
    Add a new fabric to the stash.
    Accepts nickname, fiber_content, color, print_pattern, length_meters,
    width_cm, weight_gsm, stretch, drape_structure, opacity, care_instructions,
    source_store, cost, date_acquired, suitable_garment_types, notes.
    reserved defaults to False (unassigned).
    """
    return {}


@router.get("/{fabric_id}")
def get_fabric(fabric_id: int, db: Session = Depends(get_db)):
    """
    Get a single fabric by ID, including all properties,
    linked projects (candidate and reserved), and notes.
    """
    fabric = None  # replace with db lookup
    if not fabric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fabric {fabric_id} not found",
        )
    return fabric


@router.patch("/{fabric_id}")
def update_fabric(fabric_id: int, db: Session = Depends(get_db)):
    """
    Partially update a fabric record.
    Use this to update length after cutting, change reservation status,
    or add notes about hand feel and sewing behaviour.
    """
    fabric = None  # replace with db lookup
    if not fabric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fabric {fabric_id} not found",
        )
    return fabric


@router.delete("/{fabric_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fabric(fabric_id: int, db: Session = Depends(get_db)):
    """
    Delete a fabric from the stash.
    Also removes any project links associated with this fabric.
    """
    fabric = None  # replace with db lookup
    if not fabric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fabric {fabric_id} not found",
        )
    return None


# --- Photo ---

@router.post("/{fabric_id}/photo", status_code=status.HTTP_201_CREATED)
def upload_photo(
    fabric_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload or replace the photo for a fabric.
    Accepts image/jpeg, image/png, image/webp.
    Stores the file and saves the path on the fabric record.
    """
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Use JPEG, PNG, or WebP.",
        )
    return {"filename": file.filename}


@router.delete("/{fabric_id}/photo", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(fabric_id: int, db: Session = Depends(get_db)):
    """Remove the photo from a fabric record."""
    return None


# --- Reservation ---

@router.put("/{fabric_id}/reserve/{project_id}")
def reserve_for_project(fabric_id: int, project_id: int, db: Session = Depends(get_db)):
    """
    Reserve a fabric for a specific project.
    Sets reserved=True and records the project as the primary reservation.
    A fabric can only be reserved for one project at a time.
    """
    return {}


@router.delete("/{fabric_id}/reserve", status_code=status.HTTP_204_NO_CONTENT)
def release_reservation(fabric_id: int, db: Session = Depends(get_db)):
    """
    Release a fabric reservation, returning it to available status.
    Does not delete the candidate project link — only clears the reservation flag.
    """
    return None


# --- Suitability ---

@router.get("/{fabric_id}/suitable-projects")
def get_suitable_projects(fabric_id: int, db: Session = Depends(get_db)):
    """
    Return projects whose garment type overlaps with
    this fabric's suitable_garment_types tags.
    Useful for the 'link to project' suggestion flow.
    """
    return []
