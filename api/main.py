import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api import models  # noqa: F401  -- register models with Base.metadata
from api.database import Base, engine
from api.routers import fabrics, makes, measurements, patterns, projects
from api.storage import MEDIA_URL_PREFIX, ensure_upload_dir

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Seam API", version="0.1.0")

_allowed_origins = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    MEDIA_URL_PREFIX,
    StaticFiles(directory=str(ensure_upload_dir())),
    name="media",
)

app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(fabrics.router, prefix="/fabrics", tags=["fabrics"])
app.include_router(patterns.router, prefix="/patterns", tags=["patterns"])
app.include_router(measurements.router, prefix="/measurements", tags=["measurements"])
app.include_router(makes.router, prefix="/makes", tags=["makes"])


@app.get("/health")
def health():
    return {"status": "ok"}
