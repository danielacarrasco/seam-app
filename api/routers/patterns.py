from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from api.database import get_db

router = APIRouter()


@router.get("/")
def list_patterns(
    brand: Optional[str] = None,
    garment_type: Optional[str] = None,
    previously_used: Optional[bool] = None,
    would_remake: Optional[bool] = None,
    size: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    List all patterns in the library with optional filters.
    previously_used=True returns patterns that have at least one finished make.
    would_remake filters on the aggregate flag from finished make records.
    """
    return []


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_pattern(db: Session = Depends(get_db)):
    """
    Add a new pattern to the library.
    Accepts brand, designer, pattern_name, pattern_number, garment_type,
    size_chosen, size_range, view_version, recommended_fabrics,
    instructions_rating (1–5), notes.
    previously_used defaults to False.
    """
    return {}


@router.get("/{pattern_id}")
def get_pattern(pattern_id: int, db: Session = Depends(get_db)):
    """
    Get a single pattern by ID.
    Includes all fields, fit history entries, and linked finished makes.
    """
    pattern = None  # replace with db lookup
    if not pattern:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pattern {pattern_id} not found",
        )
    return pattern


@router.patch("/{pattern_id}")
def update_pattern(pattern_id: int, db: Session = Depends(get_db)):
    """
    Partially update a pattern record.
    Use this to update fit notes, alterations made, or instructions rating
    after using the pattern for the first time.
    """
    pattern = None  # replace with db lookup
    if not pattern:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pattern {pattern_id} not found",
        )
    return pattern


@router.delete("/{pattern_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pattern(pattern_id: int, db: Session = Depends(get_db)):
    """
    Delete a pattern from the library.
    Does not delete linked projects or finished makes —
    only removes the pattern record and its project links.
    """
    pattern = None  # replace with db lookup
    if not pattern:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pattern {pattern_id} not found",
        )
    return None


# --- Envelope image ---

@router.post("/{pattern_id}/image", status_code=status.HTTP_201_CREATED)
def upload_envelope_image(
    pattern_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload or replace the envelope or line-drawing image for a pattern.
    Accepts image/jpeg, image/png, image/webp.
    """
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Use JPEG, PNG, or WebP.",
        )
    return {"filename": file.filename}


@router.delete("/{pattern_id}/image", status_code=status.HTTP_204_NO_CONTENT)
def delete_envelope_image(pattern_id: int, db: Session = Depends(get_db)):
    """Remove the envelope image from a pattern record."""
    return None


# --- Fit history ---

@router.get("/{pattern_id}/fit-history")
def get_fit_history(pattern_id: int, db: Session = Depends(get_db)):
    """
    Return all fit history entries for a pattern across all makes,
    ordered from most recent to oldest.
    This is the accumulating fit knowledge for the pattern.
    """
    return []


@router.post("/{pattern_id}/fit-history", status_code=status.HTTP_201_CREATED)
def add_fit_history_entry(pattern_id: int, db: Session = Depends(get_db)):
    """
    Add a fit history entry to a pattern.
    Accepts alterations_made, fit_notes, size_used, linked_make_id.
    Typically called automatically when a finished make is archived.
    """
    return {}


@router.delete("/{pattern_id}/fit-history/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fit_history_entry(
    pattern_id: int, entry_id: int, db: Session = Depends(get_db)
):
    """Delete a single fit history entry."""
    return None
