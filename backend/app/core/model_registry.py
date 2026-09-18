from dataclasses import dataclass
from enum import Enum


class ModelTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class ModelProfile:
    tier: ModelTier
    model_name: str
    display_name: str
    parameter_size: str
    compute_score: int
    expected_speed: str
    description: str


MODEL_REGISTRY: dict[ModelTier, ModelProfile] = {
    ModelTier.LOW: ModelProfile(
        tier=ModelTier.LOW,
        model_name="qwen3:1.7b",
        display_name="Qwen3 1.7B",
        parameter_size="1.7B",
        compute_score=1,
        expected_speed="fast",
        description=(
            "Lightweight model for extraction, classification, "
            "formatting, simple transformations, and basic Q&A."
        ),
    ),

    ModelTier.MEDIUM: ModelProfile(
        tier=ModelTier.MEDIUM,
        model_name="qwen3:4b",
        display_name="Qwen3 4B",
        parameter_size="4B",
        compute_score=2,
        expected_speed="balanced",
        description=(
            "Balanced model for summarization, explanations, "
            "general coding, and moderate reasoning."
        ),
    ),

    ModelTier.HIGH: ModelProfile(
        tier=ModelTier.HIGH,
        model_name="qwen3:8b",
        display_name="Qwen3 8B",
        parameter_size="8B",
        compute_score=4,
        expected_speed="slower",
        description=(
            "Strongest AURA tier for complex reasoning, debugging, "
            "analysis, and difficult multi-step tasks."
        ),
    ),
}


def get_model_by_tier(tier: ModelTier) -> ModelProfile:
    return MODEL_REGISTRY[tier]


def get_all_models() -> list[ModelProfile]:
    return list(MODEL_REGISTRY.values())
