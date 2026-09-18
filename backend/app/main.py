from fastapi import FastAPI

from app.api.ollama import router as ollama_router


app = FastAPI(
    title="AURA API",
    description="Adaptive Unified Routing Architecture for Multi-LLM Systems",
    version="0.1.0",
)

app.include_router(ollama_router)


@app.get("/")
def root():
    return {
        "name": "AURA",
        "full_name": "Adaptive Unified Routing Architecture",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "aura-backend",
    }
