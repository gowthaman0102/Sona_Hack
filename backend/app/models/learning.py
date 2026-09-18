from pydantic import BaseModel, Field


class LearningOutcome(BaseModel):
    task_type: str
    tier: str
    model_name: str

    success: bool

    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    latency_seconds: float = Field(
        ge=0.0,
    )

    normalized_compute_cost: float = Field(
        ge=0.0,
    )


class PerformanceStats(BaseModel):
    task_type: str
    tier: str

    attempts: int = 0
    successes: int = 0
    failures: int = 0

    average_confidence: float = 0.0
    average_latency_seconds: float = 0.0
    average_normalized_compute_cost: float = 0.0

    reliability_score: float = 0.5


class TierReliability(BaseModel):
    tier: str
    attempts: int
    reliability_score: float


class LearningRecommendation(BaseModel):
    task_type: str

    baseline_tier: str
    recommended_tier: str

    learning_applied: bool

    reason: str

    candidates: list[TierReliability]
