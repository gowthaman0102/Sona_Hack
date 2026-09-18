from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=1,
        description="User query to analyze before model routing.",
    )


class QueryFeatures(BaseModel):
    word_count: int
    has_code: bool
    has_reasoning_markers: bool
    has_multiple_requirements: bool


class QueryAnalysis(BaseModel):
    task_type: str
    complexity_score: int
    reasoning_required: bool
    recommended_tier: str
    explanation: str
    features: QueryFeatures
