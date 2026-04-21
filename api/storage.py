import os
import secrets
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status


UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads")).resolve()
MEDIA_URL_PREFIX = "/media"

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
_EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def ensure_upload_dir(subdir: str = "") -> Path:
    target = UPLOAD_DIR / subdir if subdir else UPLOAD_DIR
    target.mkdir(parents=True, exist_ok=True)
    return target


def save_image(file: UploadFile, subdir: str) -> str:
    """Persist an uploaded image and return a relative media path (e.g. 'fabrics/ab12.jpg')."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Use JPEG, PNG, or WebP.",
        )
    ext = _EXTENSIONS[file.content_type]
    target_dir = ensure_upload_dir(subdir)
    name = f"{secrets.token_hex(8)}{ext}"
    dest = target_dir / name
    with dest.open("wb") as out:
        while chunk := file.file.read(1024 * 1024):
            out.write(chunk)
    return f"{subdir}/{name}"


def delete_image(relative_path: Optional[str]) -> None:
    if not relative_path:
        return
    target = (UPLOAD_DIR / relative_path).resolve()
    if UPLOAD_DIR not in target.parents:
        return
    if target.exists():
        target.unlink()


def media_url(relative_path: Optional[str]) -> Optional[str]:
    if not relative_path:
        return None
    return f"{MEDIA_URL_PREFIX}/{relative_path}"
