from fastapi import (
    APIRouter,
    HTTPException,
)
from pydantic import BaseModel, Field

from app.models.decomposition import MultiTaskExecutionResult
from app.services.multi_task_router import MultiTaskRouter


class MultiRouteRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=1,
        description=(
            "A user request that may contain "
            "multiple independent tasks."
        ),
    )


router = APIRouter(
    prefix="/multi-route",
    tags=["Multi-Task Routing"],
)

multi_task_router = MultiTaskRouter()


@router.post(
    "",
    response_model=MultiTaskExecutionResult,
)
def multi_route(
    request: MultiRouteRequest,
):
    try:
        return multi_task_router.execute(
            request.prompt
        )

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                f"AURA multi-task routing failed: {exc}"
            ),
        ) from exc
