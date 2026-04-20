from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from api.database import get_db

router = APIRouter()

# Measurements belong to a single user profile.
# All routes operate on that profile rather than a collection.
# History entries are stored separately to track changes over time.


@router.get("/")
def get_measurements(db: Session = Depends(get_db)):
    """
    Return the current measurement profile.
    Includes all body measurements, preferred fit notes,
    and common alterations.
    """
    return {}


@router.put("/")
def save_measurements(db: Session = Depends(get_db)):
    """
    Create or fully replace the measurement profile.
    Accepts all measurement fields. Also saves a timestamped
    snapshot to measurement history automatically.

    Expected fields (all in cm):
    bust, waist, hips, high_bust, back_length, front_length,
    shoulder_width, sleeve_length, inseam, rise, neck,
    upper_arm, wrist, thigh, calf, height, weight (optional).

    Also accepts: preferred_ease, common_alterations (list of strings),
    fit_notes (free text).
    """
    return {}


@router.patch("/")
def update_measurements(db: Session = Depends(get_db)):
    """
    Partially update the measurement profile.
    Only provided fields are updated. Also saves a history snapshot.
    """
    return {}


# --- Common alterations ---

@router.get("/alterations")
def get_alterations(db: Session = Depends(get_db)):
    """
    Return the list of common alterations for this profile.
    Examples: 'lowered bust apex', 'swayback adjustment',
    'narrow shoulders', 'lengthen bodice 1.5cm'.
    """
    return []


@router.post("/alterations", status_code=status.HTTP_201_CREATED)
def add_alteration(db: Session = Depends(get_db)):
    """
    Add a common alteration to the profile.
    Accepts label (short string) and optional notes.
    """
    return {}


@router.delete("/alterations/{alteration_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alteration(alteration_id: int, db: Session = Depends(get_db)):
    """Remove a common alteration from the profile."""
    return None


# --- Garment-specific fit notes ---

@router.get("/fit-notes")
def list_fit_notes(
    garment_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Return garment-specific fitting notes.
    Optionally filter by garment_type (e.g. 'trouser', 'coat', 'dress').
    """
    return []


@router.post("/fit-notes", status_code=status.HTTP_201_CREATED)
def add_fit_note(db: Session = Depends(get_db)):
    """
    Add a garment-specific fit note to the profile.
    Accepts garment_type and note (free text).
    Example: garment_type='trouser', note='always need a swayback adjustment'.
    """
    return {}


@router.patch("/fit-notes/{note_id}")
def update_fit_note(note_id: int, db: Session = Depends(get_db)):
    """Update a garment-specific fit note."""
    note = None  # replace with db lookup
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fit note {note_id} not found",
        )
    return note


@router.delete("/fit-notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fit_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a garment-specific fit note."""
    return None


# --- Measurement history ---

@router.get("/history")
def get_measurement_history(db: Session = Depends(get_db)):
    """
    Return all past measurement snapshots, newest first.
    Each snapshot is a full copy of measurements at a point in time.
    Useful for tracking changes over time.
    """
    return []


@router.get("/history/{snapshot_id}")
def get_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    """Return a single historical measurement snapshot."""
    snapshot = None  # replace with db lookup
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {snapshot_id} not found",
        )
    return snapshot


@router.delete("/history/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    """Delete a historical measurement snapshot."""
    return None
