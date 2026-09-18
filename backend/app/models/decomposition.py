from pydantic import BaseModel

from app.models.confidence import (
    ConfidenceEvaluation,
    EscalationSummary,
)
from app.models.query_analysis import QueryAnalysis


class DecomposedTask(BaseModel):
    index: int
    text: str
    analysis: QueryAnalysis


class DecompositionResult(BaseModel):
    original_prompt: str
    is_multi_task: bool
    task_count: int
    reason: str
    tasks: list[DecomposedTask]


class SubtaskExecutionResult(BaseModel):
    index: int
    task: str
    task_type: str

    recommended_tier: str
    selected_tier: str
    selected_model: str

    compute_score: int
    thinking_enabled: bool

    response: str
    confidence: ConfidenceEvaluation
    escalation: EscalationSummary

    prompt_tokens: int | None = None
    output_tokens: int | None = None
    latency_seconds: float | None = None
    tokens_per_second: float | None = None


class MultiTaskExecutionResult(BaseModel):
    original_prompt: str
    is_multi_task: bool
    task_count: int

    tasks: list[SubtaskExecutionResult]

    aggregated_response: str
    total_prompt_tokens: int
    total_output_tokens: int
    total_latency_seconds: float
    total_compute_score: int
