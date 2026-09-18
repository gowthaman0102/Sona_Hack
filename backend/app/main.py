from fastapi import FastAPI

from app.api.analysis import router as analysis_router
from app.api.models import router as models_router
from app.api.ollama import router as ollama_router


app = FastAPI(
    title="AURA API",
    description="Adaptive Unified Routing Architecture for Multi-LLM Systems",
    version="0.3.0",
)

app.include_router(ollama_router)
app.include_router(models_router)
app.include_router(analysis_router)


@app.get("/")
def root():
    return {
        "name": "AURA",
        "full_name": "Adaptive Unified Routing Architecture",
        "status": "running",
        "version": "0.3.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "aura-backend",
    }
