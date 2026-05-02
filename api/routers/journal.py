import json
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from api.database import get_db
from api.image_gen import generate_fashion_sketch
from api.models import (
    JournalEntry,
    JournalProjectSuggestion,
    Project,
    Sketch,
)
from api.schemas import (
    JournalEntryCreate,
    JournalEntryRead,
    JournalEntrySummary,
    JournalEntryUpdate,
    JournalSuggestionRead,
)
from api.storage import delete_image, media_url, save_bytes, save_image
from api.text_gen import generate_project_suggestions, is_configured

router = APIRouter()
sugg_router = APIRouter()


def _serialize_entry(entry: JournalEntry) -> JournalEntry:
    entry.image_url = media_url(entry.image_path)
    entry.suggestion_count = len(entry.suggestions)
    return entry


# ---- Entries ----

@router.get("/", response_model=List[JournalEntrySummary])
def list_entries(db: Session = Depends(get_db)):
    entries = db.query(JournalEntry).order_by(JournalEntry.created_at.desc()).all()
    return [_serialize_entry(e) for e in entries]


@router.get("/ai-status")
def ai_status():
    return {"configured": is_configured()}


@router.post(
    "/", response_model=JournalEntryRead, status_code=status.HTTP_201_CREATED
)
def create_entry(payload: JournalEntryCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    entry = JournalEntry(**data)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _serialize_entry(entry)


@router.get("/{entry_id}", response_model=JournalEntryRead)
def get_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(JournalEntry, entry_id)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Journal entry {entry_id} not found")
    return _serialize_entry(entry)


@router.put("/{entry_id}", response_model=JournalEntryRead)
def update_entry(
    entry_id: int, payload: JournalEntryUpdate, db: Session = Depends(get_db)
):
    entry = db.get(JournalEntry, entry_id)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Journal entry {entry_id} not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(entry, k, v)
    db.commit()
    db.refresh(entry)
    return _serialize_entry(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(JournalEntry, entry_id)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Journal entry {entry_id} not found")
    delete_image(entry.image_path)
    db.delete(entry)
    db.commit()
    return None


@router.post("/{entry_id}/image", status_code=status.HTTP_201_CREATED)
def upload_image(
    entry_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    entry = db.get(JournalEntry, entry_id)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Journal entry {entry_id} not found")
    delete_image(entry.image_path)
    entry.image_path = save_image(file, "journal")
    db.commit()
    return {"image_url": media_url(entry.image_path)}


# ---- Suggestions ----

@router.get("/{entry_id}/suggestions", response_model=List[JournalSuggestionRead])
def list_suggestions(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(JournalEntry, entry_id)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Journal entry {entry_id} not found")
    return entry.suggestions


@router.post(
    "/{entry_id}/generate-suggestions",
    response_model=List[JournalSuggestionRead],
    status_code=status.HTTP_201_CREATED,
)
def generate_suggestions(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(JournalEntry, entry_id)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Journal entry {entry_id} not found")

    parsed = generate_project_suggestions(
        entry_type=entry.entry_type,
        title=entry.title,
        tags=entry.tags or [],
        body=entry.body,
    )
    raw = parsed.pop("_raw", None)
    saved = []
    for s in parsed.get("project_suggestions", []) or []:
        if not isinstance(s, dict) or not s.get("title"):
            continue
        suggestion = JournalProjectSuggestion(
            journal_entry_id=entry_id,
            title=str(s.get("title"))[:200],
            garment_type=(s.get("garment_type") or None),
            silhouette=(s.get("silhouette") or None),
            mood=s.get("mood") or [],
            palette=s.get("palette") or [],
            fabric_ideas=s.get("fabric_ideas") or [],
            pattern_features=s.get("pattern_features") or [],
            construction_notes=s.get("construction_notes") or [],
            sketch_prompt=s.get("sketch_prompt") or None,
            rationale=s.get("rationale") or None,
            raw_json=raw,
        )
        db.add(suggestion)
        saved.append(suggestion)
    if not saved:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "AI returned no usable suggestions."
        )
    db.commit()
    for s in saved:
        db.refresh(s)
    return saved


# ---- Suggestion actions (mounted at /journal-suggestions) ----

@sugg_router.post(
    "/{suggestion_id}/create-project",
    status_code=status.HTTP_201_CREATED,
)
def create_project_from_suggestion(
    suggestion_id: int,
    db: Session = Depends(get_db),
    status_override: Optional[str] = None,
):
    sugg = db.get(JournalProjectSuggestion, suggestion_id)
    if not sugg:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Suggestion {suggestion_id} not found")
    entry = db.get(JournalEntry, sugg.journal_entry_id)

    notes_lines = []
    if entry:
        notes_lines.append(
            f"Inspired by journal entry: {entry.title or '(untitled)'} (#{entry.id})"
        )
    if sugg.silhouette:
        notes_lines.append(f"Silhouette: {sugg.silhouette}")
    if sugg.mood:
        notes_lines.append(f"Mood: {', '.join(sugg.mood)}")
    if sugg.palette:
        notes_lines.append(f"Palette: {', '.join(sugg.palette)}")
    if sugg.fabric_ideas:
        notes_lines.append("Fabric ideas: " + ", ".join(sugg.fabric_ideas))
    if sugg.construction_notes:
        notes_lines.append("Construction: " + "; ".join(sugg.construction_notes))
    if sugg.rationale:
        notes_lines.append(f"Rationale: {sugg.rationale}")
    notes = "\n".join(notes_lines) or None

    tags = list({*(sugg.mood or []), *((entry.tags if entry else []) or [])})
    fit_considerations = (
        "; ".join(sugg.pattern_features) if sugg.pattern_features else None
    )
    planned_techniques = (
        "; ".join(sugg.construction_notes) if sugg.construction_notes else None
    )

    project = Project(
        title=sugg.title,
        garment_type=sugg.garment_type,
        status=status_override or "idea",
        notes=notes,
        category_tags=tags or [],
        planned_techniques=planned_techniques,
        fit_considerations=fit_considerations,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"project_id": project.id, "title": project.title}


@sugg_router.post(
    "/{suggestion_id}/generate-sketch",
    status_code=status.HTTP_201_CREATED,
)
def generate_sketch_from_suggestion(
    suggestion_id: int,
    project_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    sugg = db.get(JournalProjectSuggestion, suggestion_id)
    if not sugg:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Suggestion {suggestion_id} not found")
    if not sugg.sketch_prompt:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "This suggestion has no sketch prompt."
        )
    if project_id is not None and not db.get(Project, project_id):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Project {project_id} not found"
        )

    image_bytes = generate_fashion_sketch(sugg.sketch_prompt)
    path = save_bytes(image_bytes, "sketches", ".png")
    sketch = Sketch(
        source="generated",
        prompt=sugg.sketch_prompt,
        project_id=project_id,
        path=path,
    )
    db.add(sketch)
    db.commit()
    db.refresh(sketch)
    return {"sketch_id": sketch.id, "url": media_url(sketch.path)}
