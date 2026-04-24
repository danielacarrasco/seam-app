from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from typing import List, Optional

from api.database import get_db
from api.models import Fabric, Project, ProjectFabric
from api.schemas import FabricCreate, FabricRead, FabricUpdate
from api.schemas.project import ProjectSummary
from api.storage import delete_image, media_url, save_image

router = APIRouter()


def _serialize(fabric: Fabric) -> Fabric:
    fabric.photo_url = media_url(fabric.photo_path)
    return fabric


@router.get("/", response_model=List[FabricRead])
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
    q = db.query(Fabric)
    if fiber:
        q = q.filter(Fabric.fiber_content.ilike(f"%{fiber}%"))
    if color:
        q = q.filter(Fabric.color.ilike(f"%{color}%"))
    if stretch is not None:
        q = q.filter(Fabric.stretch == stretch)
    if structure:
        q = q.filter(Fabric.drape_structure == structure)
    if reserved is not None:
        q = q.filter(Fabric.reserved == reserved)
    if min_length is not None:
        q = q.filter(Fabric.length_meters >= min_length)
    fabrics = q.order_by(Fabric.created_at.desc()).all()
    if suitable_for:
        fabrics = [
            f for f in fabrics
            if suitable_for in (f.suitable_garment_types or [])
        ]
    return [_serialize(f) for f in fabrics]


@router.post("/", response_model=FabricRead, status_code=status.HTTP_201_CREATED)
def create_fabric(payload: FabricCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    fabric = Fabric(**data)
    db.add(fabric)
    db.commit()
    db.refresh(fabric)
    return _serialize(fabric)


@router.get("/{fabric_id}", response_model=FabricRead)
def get_fabric(fabric_id: int, db: Session = Depends(get_db)):
    fabric = db.get(Fabric, fabric_id)
    if not fabric:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Fabric {fabric_id} not found")
    return _serialize(fabric)


@router.patch("/{fabric_id}", response_model=FabricRead)
def update_fabric(fabric_id: int, payload: FabricUpdate, db: Session = Depends(get_db)):
    fabric = db.get(Fabric, fabric_id)
    if not fabric:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Fabric {fabric_id} not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(fabric, field, value)
    db.commit()
    db.refresh(fabric)
    return _serialize(fabric)


@router.delete("/{fabric_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fabric(fabric_id: int, db: Session = Depends(get_db)):
    fabric = db.get(Fabric, fabric_id)
    if not fabric:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Fabric {fabric_id} not found")
    delete_image(fabric.photo_path)
    db.delete(fabric)
    db.commit()
    return None


# --- Photo ---

@router.post("/{fabric_id}/photo", status_code=status.HTTP_201_CREATED)
def upload_photo(
    fabric_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    fabric = db.get(Fabric, fabric_id)
    if not fabric:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Fabric {fabric_id} not found")
    delete_image(fabric.photo_path)
    fabric.photo_path = save_image(file, "fabrics")
    db.commit()
    return {"photo_url": media_url(fabric.photo_path)}


@router.delete("/{fabric_id}/photo", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(fabric_id: int, db: Session = Depends(get_db)):
    fabric = db.get(Fabric, fabric_id)
    if not fabric:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Fabric {fabric_id} not found")
    delete_image(fabric.photo_path)
    fabric.photo_path = None
    db.commit()
    return None


# --- Reservation ---

@router.put("/{fabric_id}/reserve/{project_id}", response_model=FabricRead)
def reserve_for_project(
    fabric_id: int, project_id: int, db: Session = Depends(get_db)
):
    fabric = db.get(Fabric, fabric_id)
    if not fabric:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Fabric {fabric_id} not found")
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")
    fabric.reserved = True
    fabric.reserved_project_id = project_id
    db.commit()
    db.refresh(fabric)
    return _serialize(fabric)


@router.delete("/{fabric_id}/reserve", status_code=status.HTTP_204_NO_CONTENT)
def release_reservation(fabric_id: int, db: Session = Depends(get_db)):
    fabric = db.get(Fabric, fabric_id)
    if not fabric:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Fabric {fabric_id} not found")
    fabric.reserved = False
    fabric.reserved_project_id = None
    db.commit()
    return None


# --- Suitability ---

@router.get("/{fabric_id}/suitable-projects", response_model=List[ProjectSummary])
def get_suitable_projects(fabric_id: int, db: Session = Depends(get_db)):
    fabric = db.get(Fabric, fabric_id)
    if not fabric:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Fabric {fabric_id} not found")
    tags = set(fabric.suitable_garment_types or [])
    if not tags:
        return []
    return (
        db.query(Project)
        .filter(Project.garment_type.in_(tags))
        .order_by(Project.created_at.desc())
        .all()
    )
