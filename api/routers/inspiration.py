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
    InspirationEntry,
    InspirationProjectSuggestion,
    Project,
    Sketch,
)
from api.schemas import (
    GenerateSuggestionRequest,
    InspirationEntryCreate,
    InspirationEntryRead,
    InspirationEntryUpdate,
    InspirationSuggestionRead,
)
from api.storage import delete_image, media_url, save_bytes, save_image
from api.text_gen import generate_project_suggestion, is_configured

router = APIRouter()
sugg_router = APIRouter()


def _serialize_entry(entry: InspirationEntry) -> InspirationEntry:
    entry.image_url = media_url(entry.image_path)
    return entry


def _entry_dict(entry: InspirationEntry) -> dict:
    return {
        "id": entry.id,
        "title": entry.title,
        "entry_type": entry.entry_type,
        "body": entry.body,
        "tags": entry.tags or [],
        "image_url": media_url(entry.image_path),
    }


# ---- Status ----

@router.get("/ai-status")
def ai_status():
    return {"configured": is_configured()}


# ---- Entries ----

@router.get("/", response_model=List[InspirationEntryRead])
def list_entries(db: Session = Depends(get_db)):
    entries = db.query(InspirationEntry).order_by(InspirationEntry.created_at.desc()).all()
    return [_serialize_entry(e) for e in entries]


@router.post(
    "/", response_model=InspirationEntryRead, status_code=status.HTTP_201_CREATED
)
def create_entry(payload: InspirationEntryCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    body = (data.get("body") or "").strip() or None
    data["body"] = body
    entry = InspirationEntry(**data)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _serialize_entry(entry)


@router.get("/{entry_id}", response_model=InspirationEntryRead)
def get_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(InspirationEntry, entry_id)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Inspiration entry {entry_id} not found")
    return _serialize_entry(entry)


@router.put("/{entry_id}", response_model=InspirationEntryRead)
def update_entry(
    entry_id: int, payload: InspirationEntryUpdate, db: Session = Depends(get_db)
):
    entry = db.get(InspirationEntry, entry_id)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Inspiration entry {entry_id} not found")
    data = payload.model_dump(exclude_unset=True)
    if "body" in data:
        data["body"] = (data["body"] or "").strip() or None
    for k, v in data.items():
        setattr(entry, k, v)
    if not entry.body and not entry.image_path:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Entry needs body or image")
    db.commit()
    db.refresh(entry)
    return _serialize_entry(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(InspirationEntry, entry_id)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Inspiration entry {entry_id} not found")
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
    entry = db.get(InspirationEntry, entry_id)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Inspiration entry {entry_id} not found")
    delete_image(entry.image_path)
    entry.image_path = save_image(file, "inspiration")
    db.commit()
    return {"image_url": media_url(entry.image_path)}


@router.delete("/{entry_id}/image", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry_image(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(InspirationEntry, entry_id)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Inspiration entry {entry_id} not found")
    if not entry.body:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot remove image — entry would be empty.")
    delete_image(entry.image_path)
    entry.image_path = None
    db.commit()
    return None


# ---- Generate ----

@router.post(
    "/generate-project-suggestion",
    response_model=InspirationSuggestionRead,
    status_code=status.HTTP_201_CREATED,
)
def generate_suggestion(payload: GenerateSuggestionRequest, db: Session = Depends(get_db)):
    entries = (
        db.query(InspirationEntry)
        .filter(InspirationEntry.id.in_(payload.entry_ids))
        .all()
    )
    if not entries:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "None of the selected entries exist."
        )
    # Preserve user's selection order
    by_id = {e.id: e for e in entries}
    ordered = [by_id[i] for i in payload.entry_ids if i in by_id]

    parsed = generate_project_suggestion([_entry_dict(e) for e in ordered])
    raw = parsed.pop("_raw", None)

    suggestion = InspirationProjectSuggestion(
        title=str(parsed.get("title"))[:200],
        source_entry_ids=[e.id for e in ordered],
        garment_type=parsed.get("garment_type") or None,
        silhouette=parsed.get("silhouette") or None,
        mood=parsed.get("mood") or [],
        palette=parsed.get("palette") or [],
        imagery=parsed.get("imagery") or [],
        fabric_ideas=parsed.get("fabric_ideas") or [],
        pattern_features=parsed.get("pattern_features") or [],
        construction_notes=parsed.get("construction_notes") or [],
        fit_considerations=parsed.get("fit_considerations") or [],
        sketch_prompt=parsed.get("sketch_prompt") or None,
        rationale=parsed.get("rationale") or None,
        raw_json=raw,
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)
    return suggestion


# ---- Suggestion actions (mounted at /inspiration-suggestions) ----

@sugg_router.get("/{suggestion_id}", response_model=InspirationSuggestionRead)
def get_suggestion(suggestion_id: int, db: Session = Depends(get_db)):
    sugg = db.get(InspirationProjectSuggestion, suggestion_id)
    if not sugg:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Suggestion {suggestion_id} not found")
    return sugg


@sugg_router.post(
    "/{suggestion_id}/create-project",
    status_code=status.HTTP_201_CREATED,
)
def create_project_from_suggestion(
    suggestion_id: int,
    db: Session = Depends(get_db),
):
    sugg = db.get(InspirationProjectSuggestion, suggestion_id)
    if not sugg:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Suggestion {suggestion_id} not found")

    source_ids = sugg.source_entry_ids or []
    source_entries = (
        db.query(InspirationEntry).filter(InspirationEntry.id.in_(source_ids)).all()
        if source_ids else []
    )
    source_titles = [e.title or f"#{e.id}" for e in source_entries]
    source_tags = []
    for e in source_entries:
        for t in (e.tags or []):
            if t not in source_tags:
                source_tags.append(t)

    notes_lines = []
    if source_titles:
        notes_lines.append("Inspired by: " + ", ".join(source_titles))
    if sugg.silhouette:
        notes_lines.append(f"Silhouette: {sugg.silhouette}")
    if sugg.mood:
        notes_lines.append(f"Mood: {', '.join(sugg.mood)}")
    if sugg.palette:
        notes_lines.append(f"Palette: {', '.join(sugg.palette)}")
    if sugg.imagery:
        notes_lines.append(f"Imagery: {', '.join(sugg.imagery)}")
    if sugg.fabric_ideas:
        notes_lines.append("Fabric ideas: " + ", ".join(sugg.fabric_ideas))
    if sugg.construction_notes:
        notes_lines.append("Construction: " + "; ".join(sugg.construction_notes))
    if sugg.rationale:
        notes_lines.append(f"Rationale: {sugg.rationale}")
    notes = "\n".join(notes_lines) or None

    tags = []
    for collection in ((sugg.mood or []), (sugg.imagery or []), source_tags):
        for t in collection:
            if t and t not in tags:
                tags.append(t)

    fit_parts = list(sugg.fit_considerations or []) + list(sugg.pattern_features or [])
    project = Project(
        title=sugg.title,
        garment_type=sugg.garment_type,
        status="idea",
        notes=notes,
        category_tags=tags,
        planned_techniques=("; ".join(sugg.construction_notes) if sugg.construction_notes else None),
        fit_considerations=("; ".join(fit_parts) if fit_parts else None),
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
    sugg = db.get(InspirationProjectSuggestion, suggestion_id)
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
