from collections import Counter
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import extract
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import (
    Fabric,
    FitHistoryEntry,
    Make,
    MakePhoto,
    Pattern,
    Project,
)
from api.schemas import (
    MakeCreate,
    MakePhotoRead,
    MakeRead,
    MakeSummary,
    MakeUpdate,
)
from api.storage import delete_image, media_url, save_image

router = APIRouter()


def _serialize_photo(photo: MakePhoto) -> MakePhoto:
    photo.url = media_url(photo.path)
    return photo


def _serialize(make: Make) -> Make:
    cover = make.photos[0] if make.photos else None
    make.cover_photo_url = media_url(cover.path) if cover else None
    return make


@router.get("/", response_model=List[MakeSummary])
def list_makes(
    garment_type: Optional[str] = None,
    pattern_id: Optional[int] = None,
    fit_outcome: Optional[str] = None,
    would_remake: Optional[bool] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Make)
    if pattern_id is not None:
        q = q.filter(Make.pattern_id == pattern_id)
    if fit_outcome:
        q = q.filter(Make.fit_outcome == fit_outcome)
    if would_remake is not None:
        q = q.filter(Make.would_remake == would_remake)
    if year is not None:
        q = q.filter(extract("year", Make.created_at) == year)
    if garment_type:
        q = q.join(Make.project).filter(Project.garment_type == garment_type)
    makes = q.order_by(Make.created_at.desc()).all()
    return [_serialize(m) for m in makes]


@router.post("/", response_model=MakeRead, status_code=status.HTTP_201_CREATED)
def create_make(payload: MakeCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    make = Make(**data)
    db.add(make)
    db.flush()

    # Trigger a fit history entry on the linked pattern, as documented.
    if make.pattern_id:
        pattern = db.get(Pattern, make.pattern_id)
        if pattern:
            db.add(
                FitHistoryEntry(
                    pattern_id=pattern.id,
                    fit_notes=make.what_worked or make.what_didnt,
                    linked_make_id=make.id,
                )
            )
            pattern.previously_used = True

    db.commit()
    db.refresh(make)
    return make


@router.get("/{make_id}", response_model=MakeRead)
def get_make(make_id: int, db: Session = Depends(get_db)):
    make = db.get(Make, make_id)
    if not make:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Make {make_id} not found")
    return make


@router.patch("/{make_id}", response_model=MakeRead)
def update_make(make_id: int, payload: MakeUpdate, db: Session = Depends(get_db)):
    make = db.get(Make, make_id)
    if not make:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Make {make_id} not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(make, field, value)
    db.commit()
    db.refresh(make)
    return make


@router.delete("/{make_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_make(make_id: int, db: Session = Depends(get_db)):
    make = db.get(Make, make_id)
    if not make:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Make {make_id} not found")
    for photo in make.photos:
        delete_image(photo.path)
    db.query(FitHistoryEntry).filter_by(linked_make_id=make_id).delete()
    db.delete(make)
    db.commit()
    return None


# --- Photos ---

@router.get("/{make_id}/photos", response_model=List[MakePhotoRead])
def list_photos(make_id: int, db: Session = Depends(get_db)):
    make = db.get(Make, make_id)
    if not make:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Make {make_id} not found")
    return [_serialize_photo(p) for p in make.photos]


@router.post(
    "/{make_id}/photos",
    response_model=MakePhotoRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_photo(
    make_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    make = db.get(Make, make_id)
    if not make:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Make {make_id} not found")
    photo = MakePhoto(make_id=make_id, path=save_image(file, "makes"))
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return _serialize_photo(photo)


@router.delete(
    "/{make_id}/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_photo(make_id: int, photo_id: int, db: Session = Depends(get_db)):
    photo = db.query(MakePhoto).filter_by(id=photo_id, make_id=make_id).first()
    if photo:
        delete_image(photo.path)
        db.delete(photo)
        db.commit()
    return None


# --- Insights ---

@router.get("/insights/summary")
def get_insights(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Make)
    if year is not None:
        q = q.filter(extract("year", Make.created_at) == year)
    makes = q.all()

    total = len(makes)
    would_remake_rate = (
        sum(1 for m in makes if m.would_remake) / total if total else 0.0
    )
    fit_breakdown = Counter(m.fit_outcome for m in makes if m.fit_outcome)
    garment_counter: Counter = Counter()
    for m in makes:
        if m.project and m.project.garment_type:
            garment_counter[m.project.garment_type] += 1

    return {
        "total_makes": total,
        "would_remake_rate": round(would_remake_rate, 3),
        "fit_outcome_breakdown": {
            "good": fit_breakdown.get("good", 0),
            "needs_adjustment": fit_breakdown.get("needs_adjustment", 0),
            "poor": fit_breakdown.get("poor", 0),
        },
        "most_used_garment_types": [
            {"garment_type": gt, "count": c}
            for gt, c in garment_counter.most_common(5)
        ],
        "most_common_lessons": [
            m.lessons_learned for m in makes if m.lessons_learned
        ][:5],
    }


@router.get("/insights/patterns")
def pattern_performance(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for pattern in db.query(Pattern).all():
        makes = pattern.makes
        if not makes:
            continue
        total = len(makes)
        results.append(
            {
                "pattern_id": pattern.id,
                "pattern_name": pattern.pattern_name,
                "brand": pattern.brand,
                "make_count": total,
                "would_remake_rate": round(
                    sum(1 for m in makes if m.would_remake) / total, 3
                ),
                "good_fit_count": sum(1 for m in makes if m.fit_outcome == "good"),
            }
        )
    results.sort(
        key=lambda r: (r["would_remake_rate"], r["good_fit_count"]), reverse=True
    )
    return results
