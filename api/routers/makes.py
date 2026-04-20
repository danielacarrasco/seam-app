from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from api.database import get_db

router = APIRouter()


@router.get("/")
def list_makes(
    garment_type: Optional[str] = None,
    pattern_id: Optional[int] = None,
    fit_outcome: Optional[str] = None,
    would_remake: Optional[bool] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    List all finished makes with optional filters.
    fit_outcome accepts 'good', 'needs_adjustment', or 'poor'.
    Returns newest first by default.
    """
    return []


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_make(db: Session = Depends(get_db)):
    """
    Archive a finished make.
    Accepts project_id, fabric_id, pattern_id, construction_notes,
    fit_outcome ('good' | 'needs_adjustment' | 'poor'),
    what_worked, what_didnt, would_remake (bool),
    wear_frequency ('daily' | 'weekly' | 'occasional' | 'rarely'),
    care_outcome, lessons_learned.

    Also triggers a fit history entry on the linked pattern.
    """
    return {}


@router.get("/{make_id}")
def get_make(make_id: int, db: Session = Depends(get_db)):
    """
    Get a single finished make by ID.
    Includes all fields, photos, and links to project, fabric, and pattern.
    """
    make = None  # replace with db lookup
    if not make:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Make {make_id} not found",
        )
    return make


@router.patch("/{make_id}")
def update_make(make_id: int, db: Session = Depends(get_db)):
    """
    Partially update a finished make.
    Use this to add lessons learned after wearing the garment,
    update wear_frequency, or correct notes.
    """
    make = None  # replace with db lookup
    if not make:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Make {make_id} not found",
        )
    return make


@router.delete("/{make_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_make(make_id: int, db: Session = Depends(get_db)):
    """
    Delete a finished make record.
    Does not delete the linked project, fabric, or pattern.
    Also removes the corresponding fit history entry on the pattern.
    """
    make = None  # replace with db lookup
    if not make:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Make {make_id} not found",
        )
    return None


# --- Photos ---

@router.get("/{make_id}/photos")
def list_photos(make_id: int, db: Session = Depends(get_db)):
    """Return all photos for a finished make."""
    return []


@router.post("/{make_id}/photos", status_code=status.HTTP_201_CREATED)
def upload_photo(
    make_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a photo for a finished make.
    A make can have multiple photos.
    Accepts image/jpeg, image/png, image/webp.
    """
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Use JPEG, PNG, or WebP.",
        )
    return {"filename": file.filename}


@router.delete("/{make_id}/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(make_id: int, photo_id: int, db: Session = Depends(get_db)):
    """Delete a single photo from a finished make."""
    return None


# --- Insights ---

@router.get("/insights/summary")
def get_insights(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Return aggregate insights across all finished makes.
    Includes: total makes, most used pattern, most used fabric type,
    fit outcome breakdown, would_remake rate, most common lessons.
    Optionally filter by year.
    """
    return {
        "total_makes": 0,
        "would_remake_rate": 0.0,
        "fit_outcome_breakdown": {
            "good": 0,
            "needs_adjustment": 0,
            "poor": 0,
        },
        "most_used_garment_types": [],
        "most_common_lessons": [],
    }


@router.get("/insights/patterns")
def pattern_performance(db: Session = Depends(get_db)):
    """
    Return patterns ranked by would_remake rate and fit outcome.
    Helps the user see which patterns consistently work for them.
    """
    return []
