from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.allmodels import Base
from app.db.session import engine
from app.api.endpoints import ingest, patterns, learning, test, transactions

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Budge",
    version="1.0.0",
    description="Financial behavior pattern detection and learning system"
)

# CORS - MUST be before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(test.router, prefix="/api/v1/test", tags=["Test"])
app.include_router(ingest.router, prefix="/api/v1/ingest", tags=["Ingest"])
app.include_router(patterns.router, prefix="/api/v1/patterns", tags=["Patterns"])
app.include_router(learning.router, prefix="/api/v1/learning", tags=["Learning"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["Transactions"])

@app.get("/")
def root():
    return {
        "service": "Budge API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)