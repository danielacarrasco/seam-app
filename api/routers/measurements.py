from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Alteration, FitNote, MeasurementProfile, MeasurementSnapshot
from api.models.measurement import MEASUREMENT_FIELDS
from api.schemas import (
    AlterationCreate,
    AlterationRead,
    FitNoteCreate,
    FitNoteRead,
    FitNoteUpdate,
    MeasurementProfilePatch,
    MeasurementProfileRead,
    MeasurementProfileWrite,
    MeasurementSnapshotRead,
)

router = APIRouter()

PROFILE_ID = 1


def _get_or_create_profile(db: Session) -> MeasurementProfile:
    profile = db.get(MeasurementProfile, PROFILE_ID)
    if not profile:
        profile = MeasurementProfile(id=PROFILE_ID)
        db.add(profile)
        db.flush()
    return profile


def _snapshot(profile: MeasurementProfile, db: Session) -> None:
    data = {
        field: getattr(profile, field) for field in MEASUREMENT_FIELDS
    }
    data["preferred_ease"] = profile.preferred_ease
    data["fit_notes"] = profile.fit_notes
    db.add(MeasurementSnapshot(data=data))


@router.get("/", response_model=MeasurementProfileRead)
def get_measurements(db: Session = Depends(get_db)):
    return _get_or_create_profile(db)


@router.put("/", response_model=MeasurementProfileRead)
def save_measurements(
    payload: MeasurementProfileWrite, db: Session = Depends(get_db)
):
    profile = _get_or_create_profile(db)
    data = payload.model_dump()
    for field, value in data.items():
        setattr(profile, field, value)
    _snapshot(profile, db)
    db.commit()
    db.refresh(profile)
    return profile


@router.patch("/", response_model=MeasurementProfileRead)
def update_measurements(
    payload: MeasurementProfilePatch, db: Session = Depends(get_db)
):
    profile = _get_or_create_profile(db)
    data = payload.model_dump(exclude_unset=True)
    if not data:
        return profile
    for field, value in data.items():
        setattr(profile, field, value)
    _snapshot(profile, db)
    db.commit()
    db.refresh(profile)
    return profile


# --- Common alterations ---

@router.get("/alterations", response_model=List[AlterationRead])
def get_alterations(db: Session = Depends(get_db)):
    return db.query(Alteration).order_by(Alteration.created_at.desc()).all()


@router.post(
    "/alterations",
    response_model=AlterationRead,
    status_code=status.HTTP_201_CREATED,
)
def add_alteration(payload: AlterationCreate, db: Session = Depends(get_db)):
    alteration = Alteration(**payload.model_dump())
    db.add(alteration)
    db.commit()
    db.refresh(alteration)
    return alteration


@router.delete("/alterations/{alteration_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alteration(alteration_id: int, db: Session = Depends(get_db)):
    alteration = db.get(Alteration, alteration_id)
    if alteration:
        db.delete(alteration)
        db.commit()
    return None


# --- Garment-specific fit notes ---

@router.get("/fit-notes", response_model=List[FitNoteRead])
def list_fit_notes(
    garment_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(FitNote)
    if garment_type:
        q = q.filter(FitNote.garment_type == garment_type)
    return q.order_by(FitNote.created_at.desc()).all()


@router.post(
    "/fit-notes",
    response_model=FitNoteRead,
    status_code=status.HTTP_201_CREATED,
)
def add_fit_note(payload: FitNoteCreate, db: Session = Depends(get_db)):
    note = FitNote(**payload.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.patch("/fit-notes/{note_id}", response_model=FitNoteRead)
def update_fit_note(
    note_id: int, payload: FitNoteUpdate, db: Session = Depends(get_db)
):
    note = db.get(FitNote, note_id)
    if not note:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Fit note {note_id} not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(note, field, value)
    db.commit()
    db.refresh(note)
    return note


@router.delete("/fit-notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fit_note(note_id: int, db: Session = Depends(get_db)):
    note = db.get(FitNote, note_id)
    if note:
        db.delete(note)
        db.commit()
    return None


# --- Measurement history ---

@router.get("/history", response_model=List[MeasurementSnapshotRead])
def get_measurement_history(db: Session = Depends(get_db)):
    return (
        db.query(MeasurementSnapshot)
        .order_by(MeasurementSnapshot.created_at.desc())
        .all()
    )


@router.get("/history/{snapshot_id}", response_model=MeasurementSnapshotRead)
def get_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    snapshot = db.get(MeasurementSnapshot, snapshot_id)
    if not snapshot:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Snapshot {snapshot_id} not found"
        )
    return snapshot


@router.delete("/history/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    snapshot = db.get(MeasurementSnapshot, snapshot_id)
    if snapshot:
        db.delete(snapshot)
        db.commit()
    return None
