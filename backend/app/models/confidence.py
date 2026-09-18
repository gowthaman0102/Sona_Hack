from pydantic import BaseModel


class ConfidenceEvaluation(BaseModel):
    score: float
    level: str
    should_escalate: bool
    reasons: list[str]
    response_word_count: int


class EscalationAttempt(BaseModel):
    tier: str
    model_name: str
    confidence_score: float
    confidence_level: str
    should_escalate: bool
    reasons: list[str]


class EscalationSummary(BaseModel):
    escalated: bool
    initial_tier: str
    final_tier: str
    reason: str
    attempts: list[EscalationAttempt]
