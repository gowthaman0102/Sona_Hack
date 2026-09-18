from pydantic import BaseModel


class AttemptMetrics(BaseModel):
    tier: str
    model_name: str
    compute_score: int

    confidence_score: float
    confidence_level: str
    should_escalate: bool

    prompt_tokens: int
    output_tokens: int
    total_tokens: int

    latency_seconds: float
    tokens_per_second: float | None

    normalized_compute_cost: float


class RouteAnalytics(BaseModel):
    attempt_count: int

    total_prompt_tokens: int
    total_output_tokens: int
    total_tokens: int

    total_latency_seconds: float

    normalized_compute_cost: float

    final_attempt_compute_cost: float

    escalation_overhead_compute: float

    attempts: list[AttemptMetrics]



class MultiTaskAnalytics(BaseModel):
    task_count: int
    total_attempt_count: int

    total_prompt_tokens: int
    total_output_tokens: int
    total_tokens: int

    total_latency_seconds: float

    normalized_compute_cost: float

    final_attempt_compute_cost: float

    escalation_overhead_compute: float
