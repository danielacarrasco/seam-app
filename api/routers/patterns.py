from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from typing import List, Optional

from api.database import get_db
from api.models import FitHistoryEntry, Make, Pattern
from api.schemas import (
    FitHistoryEntryCreate,
    FitHistoryEntryRead,
    PatternCreate,
    PatternRead,
    PatternSummary,
    PatternUpdate,
)
from api.storage import delete_image, media_url, save_image

router = APIRouter()


def _serialize(pattern: Pattern) -> Pattern:
    pattern.image_url = media_url(pattern.image_path)
    return pattern


@router.get("/", response_model=List[PatternSummary])
def list_patterns(
    brand: Optional[str] = None,
    garment_type: Optional[str] = None,
    previously_used: Optional[bool] = None,
    would_remake: Optional[bool] = None,
    size: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Pattern)
    if brand:
        q = q.filter(Pattern.brand.ilike(f"%{brand}%"))
    if garment_type:
        q = q.filter(Pattern.garment_type == garment_type)
    if previously_used is not None:
        q = q.filter(Pattern.previously_used == previously_used)
    if size:
        q = q.filter(Pattern.size_chosen == size)
    patterns = q.order_by(Pattern.created_at.desc()).all()
    if would_remake is not None:
        # Aggregate across linked makes.
        patterns = [
            p for p in patterns
            if any(m.would_remake == would_remake for m in p.makes)
        ]
    return patterns


@router.post("/", response_model=PatternRead, status_code=status.HTTP_201_CREATED)
def create_pattern(payload: PatternCreate, db: Session = Depends(get_db)):
    pattern = Pattern(**payload.model_dump(exclude_unset=True))
    db.add(pattern)
    db.commit()
    db.refresh(pattern)
    return _serialize(pattern)


@router.get("/{pattern_id}", response_model=PatternRead)
def get_pattern(pattern_id: int, db: Session = Depends(get_db)):
    pattern = db.get(Pattern, pattern_id)
    if not pattern:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Pattern {pattern_id} not found")
    return _serialize(pattern)


@router.patch("/{pattern_id}", response_model=PatternRead)
def update_pattern(
    pattern_id: int, payload: PatternUpdate, db: Session = Depends(get_db)
):
    pattern = db.get(Pattern, pattern_id)
    if not pattern:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Pattern {pattern_id} not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(pattern, field, value)
    db.commit()
    db.refresh(pattern)
    return _serialize(pattern)


@router.delete("/{pattern_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pattern(pattern_id: int, db: Session = Depends(get_db)):
    pattern = db.get(Pattern, pattern_id)
    if not pattern:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Pattern {pattern_id} not found")
    delete_image(pattern.image_path)
    db.delete(pattern)
    db.commit()
    return None


# --- Envelope image ---

@router.post("/{pattern_id}/image", status_code=status.HTTP_201_CREATED)
def upload_envelope_image(
    pattern_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    pattern = db.get(Pattern, pattern_id)
    if not pattern:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Pattern {pattern_id} not found")
    delete_image(pattern.image_path)
    pattern.image_path = save_image(file, "patterns")
    db.commit()
    return {"image_url": media_url(pattern.image_path)}


@router.delete("/{pattern_id}/image", status_code=status.HTTP_204_NO_CONTENT)
def delete_envelope_image(pattern_id: int, db: Session = Depends(get_db)):
    pattern = db.get(Pattern, pattern_id)
    if not pattern:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Pattern {pattern_id} not found")
    delete_image(pattern.image_path)
    pattern.image_path = None
    db.commit()
    return None


# --- Fit history ---

@router.get("/{pattern_id}/fit-history", response_model=List[FitHistoryEntryRead])
def get_fit_history(pattern_id: int, db: Session = Depends(get_db)):
    pattern = db.get(Pattern, pattern_id)
    if not pattern:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Pattern {pattern_id} not found")
    return pattern.fit_history


@router.post(
    "/{pattern_id}/fit-history",
    response_model=FitHistoryEntryRead,
    status_code=status.HTTP_201_CREATED,
)
def add_fit_history_entry(
    pattern_id: int,
    payload: FitHistoryEntryCreate,
    db: Session = Depends(get_db),
):
    pattern = db.get(Pattern, pattern_id)
    if not pattern:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Pattern {pattern_id} not found")
    if payload.linked_make_id is not None and not db.get(Make, payload.linked_make_id):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Make {payload.linked_make_id} not found"
        )
    entry = FitHistoryEntry(
        pattern_id=pattern_id, **payload.model_dump(exclude_unset=True)
    )
    db.add(entry)
    pattern.previously_used = True
    db.commit()
    db.refresh(entry)
    return entry


@router.delete(
    "/{pattern_id}/fit-history/{entry_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_fit_history_entry(
    pattern_id: int, entry_id: int, db: Session = Depends(get_db)
):
    entry = (
        db.query(FitHistoryEntry)
        .filter_by(id=entry_id, pattern_id=pattern_id)
        .first()
    )
    if entry:
        db.delete(entry)
        db.commit()
    return None
