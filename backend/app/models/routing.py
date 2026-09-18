from typing import Literal

from pydantic import BaseModel, Field
from app.models.privacy import (
    PrivacyAssessment,
    PrivacyRoutingPolicy,
)

from app.models.confidence import (
    ConfidenceEvaluation,
    EscalationSummary,
)
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


class RoutingExplanation(BaseModel):
    summary: str
    selection_reason: str
    complexity_reason: str
    reasoning_reason: str
    compute_quality_tradeoff: str
    override_reason: str
    signals: list[str]


class RoutingDecision(BaseModel):
    recommended_tier: str
    selected_tier: str
    selected_model: str
    compute_score: int

    override_applied: bool
    thinking_override_applied: bool

    thinking_enabled: bool

    analysis: QueryAnalysis
    explanation: RoutingExplanation


class RoutedResponse(BaseModel):
    prompt: str
    routing: RoutingDecision
    response: str

    confidence: ConfidenceEvaluation | None = None
    escalation: EscalationSummary | None = None

    privacy: PrivacyAssessment | None = None
    privacy_policy: PrivacyRoutingPolicy | None = None

    prompt_tokens: int | None = None
    output_tokens: int | None = None
    latency_seconds: float | None = None
    tokens_per_second: float | None = None
