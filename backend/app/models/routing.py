from typing import Literal

from pydantic import BaseModel, Field

from app.models.query_analysis import QueryAnalysis


class RouteRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=1,
        description="User prompt to analyze and route.",
    )

    override_tier: Literal[
        "low",
        "medium",
        "high",
    ] | None = Field(
        default=None,
        description=(
            "Optional manual tier override. "
            "When omitted, AURA routes automatically."
        ),
    )

    override_thinking: bool | None = Field(
        default=None,
        description=(
            "Optional manual thinking-mode override. "
            "When omitted, AURA applies its reasoning policy."
        ),
    )


class RoutingDecision(BaseModel):
    recommended_tier: str
    selected_tier: str
    selected_model: str
    compute_score: int

    override_applied: bool
    thinking_override_applied: bool

    thinking_enabled: bool

    analysis: QueryAnalysis


class RoutedResponse(BaseModel):
    prompt: str
    routing: RoutingDecision
    response: str

    prompt_tokens: int | None = None
    output_tokens: int | None = None
    latency_seconds: float | None = None
    tokens_per_second: float | None = None
