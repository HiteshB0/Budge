from fastapi import FastAPI
from app.models.allmodels import Base
from app.db.session import engine
from app.api.endpoints import ingest, patterns, learning

app.include_router(learning.router, prefix="/api/v1", tags=["Learning"])

"""
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Budge")

app.include_router(ingest.router, prefix="/api/v1", tags=["Ingest"])
"""