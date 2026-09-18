from fastapi import (
    APIRouter,
    HTTPException,
)

from app.models.routing import (
    RouteRequest,
    RoutedResponse,
)
from app.services.intelligent_router import IntelligentRouter
from app.services.learning_context import (
    adaptive_routing_policy,
    learning_outcome_recorder,
)


router = APIRouter(
    prefix="/route",
    tags=["Intelligent Routing"],
)

intelligent_router = IntelligentRouter(
    learning_recorder=learning_outcome_recorder,
    adaptive_policy=adaptive_routing_policy,
)


@router.post(
    "",
    response_model=RoutedResponse,
)
def route_prompt(
    request: RouteRequest,
):
    try:
        return intelligent_router.route(
            prompt=request.prompt,
            override_tier=(
                request.override_tier
            ),
            override_thinking=(
                request.override_thinking
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid routing override: {exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"AURA routing failed: {exc}",
        ) from exc
