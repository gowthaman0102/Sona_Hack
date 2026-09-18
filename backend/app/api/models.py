from fastapi import APIRouter

from app.core.model_registry import get_all_models
from app.models.model_registry import (
    ModelRegistryResponse,
    RegisteredModelResponse,
)
from app.services.ollama_service import OllamaService


router = APIRouter(
    prefix="/models",
    tags=["Model Registry"],
)

ollama_service = OllamaService()


@router.get(
    "",
    response_model=ModelRegistryResponse,
)
def list_registered_models():
    installed_models = {
        model["name"]
        for model in ollama_service.list_models()
    }

    registered_models = []

    for profile in get_all_models():
        registered_models.append(
            RegisteredModelResponse(
                tier=profile.tier.value,
                model_name=profile.model_name,
                display_name=profile.display_name,
                parameter_size=profile.parameter_size,
                compute_score=profile.compute_score,
                expected_speed=profile.expected_speed,
                description=profile.description,
                installed=profile.model_name in installed_models,
            )
        )

    return ModelRegistryResponse(
        count=len(registered_models),
        models=registered_models,
    )
