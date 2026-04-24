from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.image_gen import generate_fashion_sketch
from api.models import Project, Sketch
from api.schemas import SketchGenerate, SketchRead, SketchUpdate
from api.storage import delete_image, media_url, save_bytes, save_image

router = APIRouter()


def _serialize(sketch: Sketch) -> Sketch:
    sketch.url = media_url(sketch.path) or ""
    return sketch


def _require_project(db: Session, project_id: Optional[int]) -> None:
    if project_id is not None and not db.get(Project, project_id):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Project {project_id} not found"
        )


@router.get("/", response_model=List[SketchRead])
def list_sketches(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Sketch)
    if project_id is not None:
        q = q.filter(Sketch.project_id == project_id)
    return [_serialize(s) for s in q.order_by(Sketch.created_at.desc()).all()]


@router.get("/{sketch_id}", response_model=SketchRead)
def get_sketch(sketch_id: int, db: Session = Depends(get_db)):
    sketch = db.get(Sketch, sketch_id)
    if not sketch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Sketch {sketch_id} not found")
    return _serialize(sketch)


@router.post(
    "/upload", response_model=SketchRead, status_code=status.HTTP_201_CREATED
)
def upload_sketch(
    file: UploadFile = File(...),
    project_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    _require_project(db, project_id)
    sketch = Sketch(
        source="uploaded",
        project_id=project_id,
        path=save_image(file, "sketches"),
    )
    db.add(sketch)
    db.commit()
    db.refresh(sketch)
    return _serialize(sketch)


@router.post(
    "/generate", response_model=SketchRead, status_code=status.HTTP_201_CREATED
)
def generate_sketch(payload: SketchGenerate, db: Session = Depends(get_db)):
    _require_project(db, payload.project_id)
    image_bytes = generate_fashion_sketch(payload.prompt)
    path = save_bytes(image_bytes, "sketches", ".png")
    sketch = Sketch(
        source="generated",
        prompt=payload.prompt,
        project_id=payload.project_id,
        path=path,
    )
    db.add(sketch)
    db.commit()
    db.refresh(sketch)
    return _serialize(sketch)


@router.patch("/{sketch_id}", response_model=SketchRead)
def update_sketch(
    sketch_id: int, payload: SketchUpdate, db: Session = Depends(get_db)
):
    sketch = db.get(Sketch, sketch_id)
    if not sketch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Sketch {sketch_id} not found")
    data = payload.model_dump(exclude_unset=True)
    if "project_id" in data:
        _require_project(db, data["project_id"])
        sketch.project_id = data["project_id"]
    db.commit()
    db.refresh(sketch)
    return _serialize(sketch)


@router.delete("/{sketch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sketch(sketch_id: int, db: Session = Depends(get_db)):
    sketch = db.get(Sketch, sketch_id)
    if not sketch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Sketch {sketch_id} not found")
    delete_image(sketch.path)
    db.delete(sketch)
    db.commit()
    return None
