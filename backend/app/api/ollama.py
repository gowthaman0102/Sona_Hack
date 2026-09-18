import httpx

from fastapi import APIRouter, HTTPException

from app.models.generation import GenerateRequest, GenerateResponse
from app.services.ollama_service import OllamaService


router = APIRouter(
    prefix="/ollama",
    tags=["Ollama"],
)

ollama_service = OllamaService()


@router.get("/health")
def ollama_health():
    available = ollama_service.health_check()

    return {
        "status": "available" if available else "unavailable",
        "ollama_available": available,
    }


@router.get("/models")
def ollama_models():
    try:
        models = ollama_service.list_models()

        return {
            "count": len(models),
            "models": models,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to communicate with Ollama: {exc}",
        ) from exc


@router.post(
    "/generate",
    response_model=GenerateResponse,
)
def generate_text(request: GenerateRequest):
    try:
        result = ollama_service.generate(
            model=request.model,
            prompt=request.prompt,
            system_prompt=request.system_prompt,
        )

        return GenerateResponse(**result)

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama returned an error: {exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to generate response: {exc}",
        ) from exc

