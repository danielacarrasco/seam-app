from fastapi import FastAPI
from api.routers import projects, fabrics, patterns, measurements, makes
from api.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Seam API", version="0.1.0")

app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(fabrics.router, prefix="/fabrics", tags=["fabrics"])
app.include_router(patterns.router, prefix="/patterns", tags=["patterns"])
app.include_router(measurements.router, prefix="/measurements", tags=["measurements"])
app.include_router(makes.router, prefix="/makes", tags=["makes"])

@app.get("/health")
def health():
    return {"status": "ok"}