from typing import Literal

from fastapi import APIRouter

from app.models.learning import (
    LearningRecommendation,
    PerformanceStats,
)
from app.services.learning_context import (
    adaptive_routing_policy,
    performance_history_store,
)


router = APIRouter(
    prefix="/learning",
    tags=["Adaptive Learning"],
)


@router.get(
    "/history",
    response_model=dict[str, PerformanceStats],
)
def learning_history():
    """
    Return aggregate AURA learning history.

    No prompts or model responses are stored or exposed.
    """

    return performance_history_store.snapshot()


@router.get(
    "/history/{task_type}",
    response_model=list[PerformanceStats],
)
def task_learning_history(
    task_type: str,
):
    """
    Return aggregate historical model-tier performance
    for one task type.
    """

    return performance_history_store.get_task_stats(
        task_type
    )


@router.get(
    "/recommendation/{task_type}",
    response_model=LearningRecommendation,
)
def learning_recommendation(
    task_type: str,
    baseline_tier: Literal[
        "low",
        "medium",
        "high",
    ] = "low",
):
    """
    Show the current history-aware recommendation without
    executing a model request.
    """

    return adaptive_routing_policy.recommend(
        task_type=task_type,
        baseline_tier=baseline_tier,
    )
