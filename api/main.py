import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from sqlalchemy import inspect, text

from api import models  # noqa: F401  -- register models with Base.metadata
from api.database import Base, engine
from api.routers import (
    fabrics,
    inspiration,
    makes,
    measurements,
    patterns,
    projects,
    sketches,
)
from api.storage import MEDIA_URL_PREFIX, ensure_upload_dir

Base.metadata.create_all(bind=engine)


def _ensure_columns():
    """Add nullable columns that exist in the model but not in the DB.

    Tiny migration shim so adding a new optional field on an existing
    deployment doesn't require dropping the database.
    """
    desired = {
        "makes": {"rating": "FLOAT"},
    }
    inspector = inspect(engine)
    with engine.connect() as conn:
        for table, columns in desired.items():
            if not inspector.has_table(table):
                continue
            existing = {c["name"] for c in inspector.get_columns(table)}
            for name, sql_type in columns.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}"))
        conn.commit()


_ensure_columns()

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
app.include_router(sketches.router, prefix="/sketches", tags=["sketches"])
app.include_router(inspiration.router, prefix="/inspiration", tags=["inspiration"])
app.include_router(
    inspiration.sugg_router,
    prefix="/inspiration-suggestions",
    tags=["inspiration"],
)


@app.get("/health")
def health():
    return {"status": "ok"}
